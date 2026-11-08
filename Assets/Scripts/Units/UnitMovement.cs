using System.Collections.Generic;
using UnityEngine;

public class UnitMovement : MonoBehaviour
{
    [SerializeField] private float speed = 5f;

    private Vector3 targetPosition;
    private bool hasTarget;
    private Renderer unitRenderer;
    private Color defaultColor;

    public bool IsSelected { get; private set; }

    public static readonly List<UnitMovement> AllUnits = new();

    private void OnEnable()
    {
        if (!AllUnits.Contains(this))
            AllUnits.Add(this);
    }

    private void OnDisable()
    {
        AllUnits.Remove(this);
    }

    private void Awake()
    {
        unitRenderer = GetComponent<Renderer>();

        if (unitRenderer != null &&
            unitRenderer.material.HasProperty("_BaseColor"))
        {
            defaultColor = unitRenderer.material.GetColor("_BaseColor");
        }
    }

    private void Start()
    {
        targetPosition = transform.position;
    }

    private void Update()
    {
        MoveToTarget();
    }

    public void SetSelected(bool value)
    {
        IsSelected = value;

        if (unitRenderer != null &&
            unitRenderer.material.HasProperty("_BaseColor"))
        {
            Color color = value ? Color.green : defaultColor;
            unitRenderer.material.SetColor("_BaseColor", color);
        }
    }

    public void MoveTo(Vector3 point)
    {
        targetPosition = point;
        targetPosition.y = transform.position.y;
        hasTarget = true;
    }

    public void StopMoving()
    {
        hasTarget = false;
    }

    private void MoveToTarget()
    {
        if (!hasTarget)
            return;

        Vector3 direction = targetPosition - transform.position;
        direction.y = 0f;

        if (direction.magnitude < 0.1f)
        {
            hasTarget = false;
            return;
        }

        transform.position +=
            direction.normalized * speed * Time.deltaTime;
    }
}