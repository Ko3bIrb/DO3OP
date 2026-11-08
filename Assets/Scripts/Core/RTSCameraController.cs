using UnityEngine;
using UnityEngine.InputSystem;

public class RTSCameraController : MonoBehaviour
{
    [SerializeField] private float moveSpeed = 25f;
    [SerializeField] private float minHeight = 8f;
    [SerializeField] private float maxHeight = 270f;
    [SerializeField] private float zoomSensitivity = 2f;
    [SerializeField] private float overviewCenterZ = -30f;

    private Camera mainCamera;

    private void Awake()
    {
        mainCamera = GetComponent<Camera>();
    }

    private void Update()
    {
        MoveCamera();
        ZoomCamera();
        LimitCameraPosition();
    }

    private void MoveCamera()
    {
        if (Keyboard.current == null)
            return;

        Vector3 direction = Vector3.zero;

        if (Keyboard.current.wKey.isPressed ||
            Keyboard.current.upArrowKey.isPressed)
        {
            direction += Vector3.forward;
        }

        if (Keyboard.current.sKey.isPressed ||
            Keyboard.current.downArrowKey.isPressed)
        {
            direction += Vector3.back;
        }

        if (Keyboard.current.aKey.isPressed ||
            Keyboard.current.leftArrowKey.isPressed)
        {
            direction += Vector3.left;
        }

        if (Keyboard.current.dKey.isPressed ||
            Keyboard.current.rightArrowKey.isPressed)
        {
            direction += Vector3.right;
        }

        if (direction != Vector3.zero)
        {
            transform.position +=
                direction.normalized * moveSpeed * Time.deltaTime;
        }
    }

    private void ZoomCamera()
    {
        if (Mouse.current == null || mainCamera == null)
            return;

        float scroll = Mouse.current.scroll.ReadValue().y;

        if (Mathf.Abs(scroll) < 0.01f)
            return;

        Vector2 mousePosition =
            Mouse.current.position.ReadValue();

        bool hasCursorPoint =
            TryGetWorldPoint(mousePosition, out Vector3 cursorPoint);

        float oldHeight = transform.position.y;
        float direction = Mathf.Sign(scroll);

        float newHeight =
            oldHeight - direction * zoomSensitivity * 10f;

        newHeight = Mathf.Clamp(
            newHeight,
            minHeight,
            maxHeight
        );

        Vector3 position = transform.position;
        position.y = newHeight;
        transform.position = position;

        // При приближении сохраняем точку под курсором.
        if (newHeight < oldHeight && hasCursorPoint)
        {
            if (TryGetWorldPoint(mousePosition, out Vector3 newCursorPoint))
            {
                Vector3 correction =
                    cursorPoint - newCursorPoint;

                correction.y = 0f;
                transform.position += correction;
            }
        }

        // При отдалении постепенно возвращаемся к общему обзору карты.
        if (newHeight > oldHeight)
        {
            float centerFactor = Mathf.InverseLerp(
                minHeight,
                maxHeight,
                newHeight
            );

            Vector3 centeredPosition =
                GetCenteredCameraPosition(newHeight);

            transform.position = Vector3.Lerp(
                transform.position,
                centeredPosition,
                centerFactor
            );
        }
    }

    private bool TryGetWorldPoint(
        Vector2 screenPosition,
        out Vector3 worldPoint)
    {
        Ray ray =
            mainCamera.ScreenPointToRay(screenPosition);

        if (Physics.Raycast(ray, out RaycastHit hit))
        {
            worldPoint = hit.point;
            return true;
        }

        worldPoint = Vector3.zero;
        return false;
    }

    private Vector3 GetCenteredCameraPosition(float height)
    {
        float angleRadians =
            transform.eulerAngles.x * Mathf.Deg2Rad;

        float backwardOffset =
            height / Mathf.Tan(angleRadians);

        return new Vector3(
            0f,
            height,
            overviewCenterZ - backwardOffset
        );
    }

    private void LimitCameraPosition()
    {
        Vector3 position = transform.position;

        position.x = Mathf.Clamp(
            position.x,
            -280f,
            280f
        );

        position.z = Mathf.Clamp(
            position.z,
            -230f,
            170f
        );

        transform.position = position;
    }
}