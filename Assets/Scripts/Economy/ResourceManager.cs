using UnityEngine;

public class ResourceManager : MonoBehaviour
{
    [SerializeField] private int startingGold = 0;

    private int gold;

    public int Gold => gold;

    private void Awake()
    {
        gold = startingGold;
    }

    public void AddGold(int amount)
    {
        if (amount > 0)
            gold += amount;
    }

    public bool TrySpend(int amount)
    {
        if (amount <= 0 || gold < amount)
            return false;

        gold -= amount;
        return true;
    }

    private void OnGUI()
    {
        GUI.color = Color.white;

        GUI.Label(
            new Rect(20f, 20f, 250f, 30f),
            $"Золото: {gold}"
        );
    }
}