using UnityEngine;

public class Health : MonoBehaviour
{
    [SerializeField] private float maxHealth = 100f;

    private float currentHealth;

    public float CurrentHealth => currentHealth;
    public float MaxHealth => maxHealth;

    private void Awake()
    {
        currentHealth = maxHealth;
    }

    public void IncreaseMaxHealth(float amount)
    {
        if (amount <= 0f)
            return;

        maxHealth += amount;
        currentHealth += amount;
    }

    public void TakeDamage(float damage)
    {
        if (damage <= 0f)
            return;

        currentHealth -= damage;
        currentHealth = Mathf.Max(currentHealth, 0f);

        Debug.Log(
            $"{gameObject.name} получил урон. " +
            $"Здоровье: {currentHealth}/{maxHealth}"
        );

        if (currentHealth <= 0f)
        {
            Destroy(gameObject);
        }
    }
}