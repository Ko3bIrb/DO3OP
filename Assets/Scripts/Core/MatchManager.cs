using UnityEngine;

public class MatchManager : MonoBehaviour
{
    [SerializeField] private GameObject playerCastle;
    [SerializeField] private GameObject enemyCastle;

    private bool gameOver;
    private string resultText;

    private void Awake()
    {
        Time.timeScale = 1f;
    }

    private void Update()
    {
        if (gameOver)
            return;

        if (enemyCastle == null)
        {
            FinishMatch("œŒ¡≈ƒ¿!");
        }
        else if (playerCastle == null)
        {
            FinishMatch("œŒ–¿∆≈Õ»≈");
        }
    }

    private void FinishMatch(string result)
    {
        gameOver = true;
        resultText = result;
        Time.timeScale = 0f;
    }

    private void OnGUI()
    {
        if (!gameOver)
            return;

        GUIStyle style = new GUIStyle(GUI.skin.label);
        style.fontSize = 48;
        style.alignment = TextAnchor.MiddleCenter;
        style.normal.textColor = Color.white;

        GUI.Label(
            new Rect(0f, 0f, Screen.width, Screen.height),
            resultText,
            style
        );
    }
}