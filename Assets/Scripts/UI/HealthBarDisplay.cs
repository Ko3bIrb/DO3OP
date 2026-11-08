using UnityEngine;

public class HealthBarDisplay : MonoBehaviour
{
    [SerializeField] private Vector3 offset = new Vector3(0f, 3.5f, 0f);
    [SerializeField] private Vector2 barSize = new Vector2(120f, 16f);

    private Health health;
    private Camera mainCamera;

    private void Awake()
    {
        health = GetComponent<Health>();
        mainCamera = Camera.main;
    }

    private void OnGUI()
    {
        if (health == null || mainCamera == null)
            return;

        Vector3 screenPosition = mainCamera.WorldToScreenPoint(
            transform.position + offset
        );

        if (screenPosition.z <= 0f)
            return;

        float x = screenPosition.x - barSize.x / 2f;
        float y = Screen.height - screenPosition.y - barSize.y / 2f;

        Rect background = new Rect(
            x,
            y,
            barSize.x,
            barSize.y
        );

        float healthPercent = Mathf.Clamp01(
            health.CurrentHealth / health.MaxHealth
        );

        Rect foreground = new Rect(
            x + 2f,
            y + 2f,
            (barSize.x - 4f) * healthPercent,
            barSize.y - 4f
        );

        GUI.color = Color.black;
        GUI.Box(background, GUIContent.none);

        GUI.color = Color.red;
        GUI.Box(foreground, GUIContent.none);

        GUI.color = Color.white;
        GUI.Label(
            new Rect(x, y - 22f, barSize.x, 20f),
            $"{health.CurrentHealth:0} / {health.MaxHealth:0}"
        );

        GUI.color = Color.white;
    }
}