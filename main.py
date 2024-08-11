from machine import Pin
import time
import network
import socket
import _thread

# Configuração da rede Wi-Fi
SSID = 'Wokwi-GUEST'
PASSWORD = ''

# Definição dos pinos Trig e Echo do sensor HC-SR04
trig_pin = Pin(14, Pin.OUT)  # Pino GPIO conectado ao pino Trig do sensor
echo_pin = Pin(12, Pin.IN)   # Pino GPIO conectado ao pino Echo do sensor

# Variável para armazenar a mensagem de risco
risco_msg = "situação em controle, sem riscos medidos!"

# Função para medir a distância com o sensor HC-SR04
def medir_distancia():
    global risco_msg
    # Pulsa o pino Trig por pelo menos 10µs para acionar a medição
    trig_pin.value(1)
    time.sleep_us(10)
    trig_pin.value(0)

    # Aguarda até o pino Echo se tornar alto, iniciando a contagem de tempo
    while echo_pin.value() == 0:
        pass
    start_time = time.ticks_us()

    # Aguarda até o pino Echo se tornar baixo, finalizando a contagem de tempo
    while echo_pin.value() == 1:
        pass
    end_time = time.ticks_us()

    # Calcula a duração do pulso e converte para distância em centímetros
    pulse_duration = time.ticks_diff(end_time, start_time)
    distancia_cm = (pulse_duration / 2) / 29.1  # 29.1µs/cm é o fator de conversão para o sensor HC-SR04

    return distancia_cm

# Função para atualizar o estado de risco
def atualizar_estado(distancia):
    global risco_msg
    if distancia > 300:
        risco_msg = 'risco eminente, retirem as pessoas de perto!'
    elif distancia > 100:
        risco_msg = 'risco provavel, manter cautela e atencao!'
    else:
        risco_msg = 'situação em controle, sem riscos medidos!'

# Função para conectar ao Wi-Fi
def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    while not wlan.isconnected():
        time.sleep(1)
    print('Conectado ao Wi-Fi:', wlan.ifconfig())
    return wlan.ifconfig()[0]

# Servidor Web
def servidor_web():
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print('Servidor Web rodando em', addr)

    while True:
        cl, addr = s.accept()
        print('Cliente conectado de', addr)
        request = cl.recv(1024).decode('utf-8')
        request_path = request.split(' ')[1]

        if request_path == '/risco':
            response = f"HTTP/1.1 200 OK\n\n{risco_msg}"
        else:
            response = f"""HTTP/1.1 200 OK

<html>
<head>
    <title>Sensor de Nivel</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #f0f0f0;
            color: #333;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }}
        .container {{
            background-color: #fff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            text-align: center;
            width: 300px;
        }}
        h1 {{
            color: #4CAF50;
        }}
        p {{
            font-size: 1.2em;
        }}
    </style>
    <script>
        function atualizarMensagem() {{
            fetch('/risco')
                .then(response => response.text())
                .then(data => {{
                    document.getElementById('riscoMsg').innerText = data;
                }})
                .catch(error => console.error('Erro ao atualizar a mensagem:', error));
        }}

        setInterval(atualizarMensagem, 1000); // Atualiza a cada 1 segundo
    </script>
</head>
<body>
    <div class="container">
        <h1>Estado do Risco</h1>
        <p id="riscoMsg">{risco_msg}</p>
    </div>
</body>
</html>
"""
        
        cl.send(response)
        cl.close()


# Loop principal de medição
def medir_distancia_loop():
    while True:
        distancia = medir_distancia()
        print("Nível da água: {:.2f} cm".format(distancia))
        atualizar_estado(distancia)
        time.sleep(1)

# Função principal para iniciar Wi-Fi, servidor web e loop de medição
def main():
    ip = conectar_wifi()
    print("Servidor Web acessável em: localhost:9080 ")

    # Cria uma tarefa para o servidor web
    _thread.start_new_thread(servidor_web, ())

    # Executa o loop de medição
    medir_distancia_loop()

# Executa o loop principal
main()