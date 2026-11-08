using UnityEngine;

public class CaptureZone : MonoBehaviour
{
    [SerializeField] private float radius = 1.5f;
    [SerializeField] private float captureTime = 5f;
    [SerializeField] private int goldPerSecond = 5;

    private float captureProgress;
    private bool captured;
    private float resourceTimer;

    private Camera mainCamera;
    private ResourceManager resourceManager;

    private void Awake()
    {
        mainCamera = Camera.main;
        resourceManager = FindFirstObjectByType<ResourceManager>();
    }

    private void Update()
    {
        if (captured)
        {
            GenerateResources();
            return;
        }

        bool unitInside = false;

        foreach (UnitMovement unit in UnitMovement.AllUnits)
        {
            Vector3 offset = unit.transform.position - transform.position;
            offset.y = 0f;

            if (offset.sqrMagnitude <= radius * radius)
            {
                unitInside = true;
                break;
            }
        }

        if (unitInside)
            captureProgress += Time.deltaTime / captureTime;
        else
            captureProgress -= Time.deltaTime / captureTime;

        captureProgress = Mathf.Clamp01(captureProgress);

        if (captureProgress >= 1f)
        {
            captured = true;
            Debug.Log($"{gameObject.name} çàõâà÷åíà!");
        }
    }

    private void GenerateResources()
    {
        if (resourceManager == null)
            return;

        resourceTimer += Time.deltaTime;

        if (resourceTimer >= 1f)
        {
            int seconds = Mathf.FloorToInt(resourceTimer);
            resourceManager.AddGold(goldPerSecond * seconds);
            resourceTimer -= seconds;
        }
    }

    private void OnGUI()
    {
        if (mainCamera == null)
            return;

        Vector3 screenPosition = mainCamera.WorldToScreenPoint(
            transform.position + Vector3.up * 1.5f
        );

        if (screenPosition.z <= 0f)
            return;

        string text = captured
            ? "ÇÀÕÂÀ×ÅÍÎ"
            : $"ÇÀÕÂÀÒ: {captureProgress * 100f:0}%";

        GUI.color = Color.white;

        GUI.Label(
            new Rect(
                screenPosition.x - 60f,
                Screen.height - screenPosition.y,
                150f,
                25f
            ),
            text
        );
    }
}