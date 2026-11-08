using UnityEngine;

public class UnitAttack : MonoBehaviour
{
    [SerializeField] private float attackRange = 3f;
    [SerializeField] private float damage = 10f;
    [SerializeField] private float attackInterval = 1f;

    private Health target;
    private UnitMovement movement;
    private float nextAttackTime;
    private bool hasAttackTarget;

    private void Awake()
    {
        movement = GetComponent<UnitMovement>();
    }

    private void Update()
    {
        if (!hasAttackTarget)
            return;

        if (target == null)
        {
            hasAttackTarget = false;
            movement.StopMoving();
            return;
        }

        float distance = Vector3.Distance(
            transform.position,
            target.transform.position
        );

        if (distance > attackRange)
        {
            movement.MoveTo(target.transform.position);
            return;
        }

        movement.StopMoving();

        if (Time.time >= nextAttackTime)
        {
            target.TakeDamage(damage);
            nextAttackTime = Time.time + attackInterval;
        }
    }

    public void SetTarget(Health newTarget)
    {
        target = newTarget;
        hasAttackTarget = true;
        nextAttackTime = 0f;
    }

    public void ClearTarget()
    {
        target = null;
        hasAttackTarget = false;
    }
}