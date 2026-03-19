




import pyautogui


import time

def capturar_retangulos_e_gerar_linhas():
    print("Posicione o mouse no canto superior esquerdo do primeiro elemento e pressione Enter. Depois, no canto inferior direito e pressione Enter. Repita para o segundo elemento. Pressione ESC para sair.")
    try:
        import keyboard
    except ImportError:
        print("Você precisa instalar o pacote 'keyboard': pip install keyboard")
        return









    coords = []
    for i in range(2):
        while True:
            if keyboard.is_pressed('esc'):
                print("\nFinalizado.")
                return
            if keyboard.is_pressed('enter'):
                x1, y1 = pyautogui.position()
                print(f"Canto superior esquerdo do item {i+1}: x={x1}, y={y1}")
                time.sleep(0.5)
                break
        while True:
            if keyboard.is_pressed('esc'):
                print("\nFinalizado.")
                return
            if keyboard.is_pressed('enter'):
                x2, y2 = pyautogui.position()
                print(f"Canto inferior direito do item {i+1}: x={x2}, y={y2}")
                coords.append({'l': x1, 't': y1, 'r': x2, 'b': y2})
                print(f"Retângulo {i+1}: {{l:{x1}, t:{y1}, r:{x2}, b:{y2}}}")
                time.sleep(0.5)
                break

    # Geração automática das próximas linhas
    n = 33
    delta_y = coords[1]['t'] - coords[0]['t']
    altura = coords[0]['b'] - coords[0]['t']
    l = coords[0]['l']
    r = coords[0]['r']
    retangulos = []
    for i in range(n):
        t = coords[0]['t'] + i * delta_y
        b = t + altura
        retangulos.append({'l': l, 't': t, 'r': r, 'b': b})

    print("\nRetângulos das 33 linhas:")
    for idx, rect in enumerate(retangulos):
        print(f"Linha {idx+1}: {{l:{rect['l']}, t:{rect['t']}, r:{rect['r']}, b:{rect['b']}}}")

if __name__ == "__main__":
    capturar_retangulos_e_gerar_linhas() 