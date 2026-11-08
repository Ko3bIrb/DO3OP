using UnityEngine;
using UnityEngine.InputSystem;

public class RTSSelectionManager : MonoBehaviour
{
    [SerializeField] private float dragThreshold = 10f;

    private Camera mainCamera;
    private bool isDragging;
    private Vector2 dragStart;
    private Vector2 currentMousePosition;

    private void Awake()
    {
        mainCamera = Camera.main;
    }

    private void Update()
    {
        if (mainCamera == null)
            mainCamera = Camera.main;

        if (Mouse.current == null || mainCamera == null)
            return;

        currentMousePosition = Mouse.current.position.ReadValue();

        if (Mouse.current.leftButton.wasPressedThisFrame)
        {
            dragStart = currentMousePosition;
            isDragging = true;
        }

        if (Mouse.current.leftButton.wasReleasedThisFrame && isDragging)
        {
            isDragging = false;

            float distance = Vector2.Distance(
                dragStart,
                currentMousePosition
            );

            if (distance < dragThreshold)
                SelectSingle(currentMousePosition);
            else
                SelectInBox(dragStart, currentMousePosition);
        }

        if (Mouse.current.rightButton.wasPressedThisFrame)
        {
            MoveSelectedUnits();
        }
    }

    private void SelectSingle(Vector2 screenPosition)
    {
        DeselectAll();

        Ray ray = mainCamera.ScreenPointToRay(screenPosition);

        if (Physics.Raycast(ray, out RaycastHit hit))
        {
            UnitMovement unit =
                hit.collider.GetComponentInParent<UnitMovement>();

            if (unit != null)
                unit.SetSelected(true);
        }
    }

    private void SelectInBox(Vector2 start, Vector2 end)
    {
        DeselectAll();

        Rect selectionRect = GetScreenRect(start, end);

        foreach (UnitMovement unit in UnitMovement.AllUnits)
        {
            Vector3 screenPosition =
                mainCamera.WorldToScreenPoint(unit.transform.position);

            if (screenPosition.z > 0 &&
                selectionRect.Contains(
                    new Vector2(screenPosition.x, screenPosition.y)))
            {
                unit.SetSelected(true);
            }
        }
    }

    private void MoveSelectedUnits()
    {
        Ray ray = mainCamera.ScreenPointToRay(currentMousePosition);

        if (!Physics.Raycast(ray, out RaycastHit hit))
            return;

        Health target = hit.collider.GetComponentInParent<Health>();

        if (target != null)
        {
            foreach (UnitMovement unit in UnitMovement.AllUnits)
            {
                if (!unit.IsSelected)
                    continue;

                UnitAttack attack = unit.GetComponent<UnitAttack>();

                if (attack != null)
                    attack.SetTarget(target);
            }

            return;
        }

        int selectedCount = 0;

        foreach (UnitMovement unit in UnitMovement.AllUnits)
        {
            if (unit.IsSelected)
                selectedCount++;
        }

        int index = 0;
        int columns = Mathf.CeilToInt(Mathf.Sqrt(selectedCount));

        foreach (UnitMovement unit in UnitMovement.AllUnits)
        {
            if (!unit.IsSelected)
                continue;

            UnitAttack attack = unit.GetComponent<UnitAttack>();

            if (attack != null)
                attack.ClearTarget();

            Vector3 offset = Vector3.zero;

            if (selectedCount > 1)
            {
                int row = index / columns;
                int column = index % columns;
                float center = (columns - 1) * 0.5f;

                offset = new Vector3(
                    (column - center) * 1.5f,
                    0f,
                    row * 1.5f
                );
            }

            unit.MoveTo(hit.point + offset);
            index++;
        }
    }

    private void DeselectAll()
    {
        foreach (UnitMovement unit in UnitMovement.AllUnits)
        {
            unit.SetSelected(false);
        }
    }

    private Rect GetScreenRect(Vector2 start, Vector2 end)
    {
        return Rect.MinMaxRect(
            Mathf.Min(start.x, end.x),
            Mathf.Min(start.y, end.y),
            Mathf.Max(start.x, end.x),
            Mathf.Max(start.y, end.y)
        );
    }

    private void OnGUI()
    {
        if (!isDragging ||
            Vector2.Distance(dragStart, currentMousePosition)
            < dragThreshold)
            return;

        Rect rect = GetScreenRect(
            dragStart,
            currentMousePosition
        );

        Rect guiRect = new Rect(
            rect.xMin,
            Screen.height - rect.yMax,
            rect.width,
            rect.height
        );

        Color oldColor = GUI.color;
        GUI.color = new Color(0.2f, 1f, 0.2f, 0.25f);
        GUI.Box(guiRect, GUIContent.none);
        GUI.color = oldColor;
    }
}