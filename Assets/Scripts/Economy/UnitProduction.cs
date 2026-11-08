using UnityEngine;

public class UnitProduction : MonoBehaviour
{
    [SerializeField] private GameObject unitPrefab;
    [SerializeField] private int unitCost = 10;
    [SerializeField] private float spawnDistance = 5f;

    private ResourceManager resourceManager;
    private PopulationManager populationManager;

    private void Awake()
    {
        resourceManager = FindFirstObjectByType<ResourceManager>();
        populationManager = FindFirstObjectByType<PopulationManager>();
    }

    private void OnGUI()
    {
        if (resourceManager == null || populationManager == null)
            return;

        if (GUI.Button(
            new Rect(20f, 65f, 220f, 35f),
            $"Нанять юнита ({unitCost} золота)"
        ))
        {
            SpawnUnit();
        }
    }

    private void SpawnUnit()
    {
        if (unitPrefab == null)
        {
            Debug.LogError("Unit Prefab не назначен.");
            return;
        }

        if (!populationManager.CanAddUnit())
        {
            Debug.Log("Достигнут лимит населения.");
            return;
        }

        if (!resourceManager.TrySpend(unitCost))
        {
            Debug.Log("Недостаточно золота.");
            return;
        }

        Vector3 spawnPosition =
            transform.position + transform.forward * spawnDistance;

        spawnPosition.y = 1f;

        Instantiate(
            unitPrefab,
            spawnPosition,
            Quaternion.identity
        );
    }
}