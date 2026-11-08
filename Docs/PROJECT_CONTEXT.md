# Project context for AI agents

## Current state

This is a Unity 6.6 URP RTS prototype. The playable scene is `Assets/Scenes/GlobalMap.unity`. Primitive capsules represent units and cubes/cylinders represent the first map objects.

## Systems

- `Assets/Scripts/Core/RTSCameraController.cs` — RTS camera, WASD/arrows, zoom.
- `Assets/Scripts/Core/MatchManager.cs` — victory and defeat.
- `Assets/Scripts/Units/UnitMovement.cs` — unit registration, selection state and movement.
- `Assets/Scripts/Commands/RTSSelectionManager.cs` — click/rectangle selection and right-click orders.
- `Assets/Scripts/Combat/UnitAttack.cs` — attack orders and damage timing.
- `Assets/Scripts/Combat/Health.cs` — HP and destruction.
- `Assets/Scripts/Buildings/CaptureZone.cs` — capture progress and gold generation.
- `Assets/Scripts/Buildings/CastleUpgrade.cs` — castle upgrade.
- `Assets/Scripts/Economy/ResourceManager.cs` — gold.
- `Assets/Scripts/Economy/PopulationManager.cs` — population limit.
- `Assets/Scripts/Economy/UnitProduction.cs` — unit production.
- `Assets/Scripts/UI/HealthBarDisplay.cs` — prototype HP display.

## Rules for changes

- Keep application source under `Assets` and preserve Unity `.meta` files.
- Do not commit `Library`, `Temp`, `Obj`, `Build`, or `Logs`.
- Keep gameplay logic separate from visual models.
- Prefer additive changes and preserve the working `GlobalMap` scene.
- Use ScriptableObjects for future balance data.
- Test the GlobalMap scene after gameplay changes.
