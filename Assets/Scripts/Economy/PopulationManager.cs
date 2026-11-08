using UnityEngine;

public class PopulationManager : MonoBehaviour
{
    [SerializeField] private int maxPopulation = 20;

    public int CurrentPopulation =>
        UnitMovement.AllUnits.Count;

    public int MaxPopulation =>
        maxPopulation;

    public bool CanAddUnit()
    {
        return CurrentPopulation < MaxPopulation;
    }

    public void IncreaseMaxPopulation(int amount)
    {
        if (amount > 0)
            maxPopulation += amount;
    }

    private void OnGUI()
    {
        GUI.color = Color.white;

        GUI.Label(
            new Rect(20f, 35f, 250f, 25f),
            $"Армия: {CurrentPopulation}/{MaxPopulation}"
        );
    }
}