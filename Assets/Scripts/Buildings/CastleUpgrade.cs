using UnityEngine;

public class CastleUpgrade : MonoBehaviour
{
    [SerializeField] private int upgradeCost = 50;
    [SerializeField] private int populationIncrease = 10;
    [SerializeField] private float healthIncrease = 50f;

    private ResourceManager resourceManager;
    private PopulationManager populationManager;
    private Health health;
    private bool upgraded;

    private void Awake()
    {
        resourceManager = FindFirstObjectByType<ResourceManager>();
        populationManager = FindFirstObjectByType<PopulationManager>();
        health = GetComponent<Health>();
    }

    private void OnGUI()
    {
        if (upgraded || resourceManager == null)
            return;

        if (GUI.Button(
            new Rect(20f, 105f, 220f, 35f),
            $"Улучшить замок ({upgradeCost} золота)"
        ))
        {
            Upgrade();
        }
    }

    private void Upgrade()
    {
        if (!resourceManager.TrySpend(upgradeCost))
        {
            Debug.Log("Недостаточно золота для улучшения замка.");
            return;
        }

        if (populationManager != null)
            populationManager.IncreaseMaxPopulation(populationIncrease);

        if (health != null)
            health.IncreaseMaxHealth(healthIncrease);

        transform.localScale *= 1.2f;
        upgraded = true;

        Debug.Log("Замок улучшен!");
    }
}