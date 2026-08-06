import discord
from discord.ext import commands
import random
import os
import requests
import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='$', intents=intents)

reto_usado = {}

def get_class(model_path, labels_path, image_path):
    try:
        from ultralytics import YOLO
        
        if os.path.exists(model_path):
            model = YOLO(model_path)
        else:
            model = YOLO("yolov8n.pt") 

        results = model(image_path)
        
        objetos_detectados = []
        for r in results:
            for c in r.boxes.cls:
                class_name = model.names[int(c)]
                objetos_detectados.append(class_name)
                
        return list(set(objetos_detectados))
    except ImportError:
        return ["Error_Import"]
    except Exception as e:
        print(f"Error en el proceso de inferencia: {e}")
        return []

@bot.event
async def on_ready():
    print("EcoBot_Avanzado preparado la mision como " + str(bot.user))
    mensaje_inicio = (
        "EcoBot se ha iniciado correctamente.\n"
        "EcoBot es un bot creado para cuidar el medio ambiente y transmitir a el mundo el mensaje de: Pequeñas acciones logran un GRAN Futuro\n"
        "Comandos disponibles:\n"
        "- $hello: Saludo basico.\n"
        "- $bye: Despedida.\n"
        "- $password: Genera una contrasena aleatoria.\n"
        "- $emoji: Envia una expresion de texto.\n"
        "- $joined @usuario: Muestra la fecha de ingreso de un miembro.\n"
        "- $meme: Muestra un meme local.\n"
        "- $memeapi: Obtiene un meme en linea.\n"
        "- $dog: Muestra la foto de un perro.\n"
        "- $cargar_imagen: Analiza una imagen adjunta para clasificar residuos.\n"
        "- $eco_accion: Valida una eco-accion mediante la deteccion de elementos multiples.\n"
        "- $reto: Otorga un eco-reto diario.\n"
        "- $basura: Calcula tu nivel de residuos diarios."
    )
    
    for guild in bot.guilds:
        canal_enviado = False
        if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
            try:
                await guild.system_channel.send(mensaje_inicio)
                canal_enviado = True
            except:
                pass
        
        if not canal_enviado:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    try:
                        await channel.send(mensaje_inicio)
                        break
                    except:
                        continue

@bot.event
async def on_member_join(member):
    canal = member.guild.system_channel
    if canal:
        await canal.send(f"Hola {member.mention}! Soy el EcoBot. Usa $help para ver mis comandos.")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("No conozco ese comando. Usa $help para ver mis comandos.")

@bot.command()
async def hello(ctx):
    await ctx.send("Hi!")

@bot.command()
async def bye(ctx):
    await ctx.send(":-)")

@bot.command()
async def password(ctx):
    caracteres = "+-/*!&$#?=@<>"
    password = ""

    for i in range(10):
        password += random.choice(caracteres)

    await ctx.send("Tu contrasena es: " + password)

@bot.command()
async def emoji(ctx):
    emojis = [":)", ":D", "xD", ";)"]
    await ctx.send(random.choice(emojis))

@bot.command()
async def joined(ctx, member: discord.Member):
    fecha = member.joined_at
    await ctx.send(member.name + " se unio el " + str(fecha))

@bot.command()
async def meme(ctx):
    carpeta = "images"

    comunes = ["Mem1.jpeg","Mem2.jpeg"]
    raros = ["Mem3.jpeg"]
    legendarios = ["Mem4.jpeg"]

    prob = random.randint(1,100)

    if prob <= 70:
        meme = random.choice(comunes)
        tipo = "Meme comun"

    elif prob <= 95:
        meme = random.choice(raros)
        tipo = "Meme raro"

    else:
        meme = random.choice(legendarios)
        tipo = "MEME LEGENDARIO"

    ruta = f"{carpeta}/{meme}"

    if not os.path.exists(ruta):
        await ctx.send("No encuentro ese meme en la carpeta images.")
        return

    with open(ruta, "rb") as f:
        picture = discord.File(f)

    await ctx.send(tipo)
    await ctx.send(file=picture)

@bot.command()
async def memeapi(ctx):
    url = "https://meme-api.com/gimme"
    res = requests.get(url)
    data = res.json()

    meme = data["url"]
    titulo = data["title"]

    embed = discord.Embed(title=titulo)
    embed.set_image(url=meme)

    await ctx.send(embed=embed)

@bot.command()
async def dog(ctx):
    url = "https://dog.ceo/api/breeds/image/random"
    res = requests.get(url)
    data = res.json()

    await ctx.send(data["message"])

@bot.command()
async def cargar_imagen(ctx):
    if len(ctx.message.attachments) == 0:
        await ctx.send("Clasificador de Residuos: Debes adjuntar una imagen junto con el comando $cargar_imagen para que la analice y detecte objetos de basura o reciclaje.")
        return

    for attachment in ctx.message.attachments:
        nombre_archivo = attachment.filename
        
        extensiones_validas = ('.png', '.jpg', '.jpeg', '.webp')
        if not nombre_archivo.lower().endswith(extensiones_validas):
            await ctx.send("Formato de archivo incorrecto. Por favor, envia una imagen valida (PNG, JPG, JPEG).")
            continue

        carpeta = "images_cargadas"
        
        if not os.path.exists(carpeta):
            os.makedirs(carpeta)
            
        ruta_guardado = os.path.join(carpeta, nombre_archivo)
        
        try:
            await attachment.save(ruta_guardado)
            await ctx.send("Analizando la imagen, un momento por favor...")

            model_path = "model/model.pt"
            labels_path = "model/labels.txt"

            resultado = get_class(model_path=model_path, labels_path=labels_path, image_path=ruta_guardado)

            if not resultado:
                await ctx.send("Lo siento, no estoy seguro de lo que se muestra en la imagen.")
            elif "Error_Import" in resultado:
                await ctx.send("Error: Para usar la IA necesitas instalar ultralytics. Deten el bot y ejecuta en tu terminal: pip install ultralytics")
            else:
                contenedores = {
                    "bottle": "Contenedor Amarillo (Envases plasticos/latas) o Verde (Vidrio)",
                    "cup": "Contenedor Amarillo (si es de plastico) o Gris (Resto)",
                    "apple": "Contenedor Marron (Organico)",
                    "banana": "Contenedor Marron (Organico)",
                    "orange": "Contenedor Marron (Organico)",
                    "broccoli": "Contenedor Marron (Organico)",
                    "carrot": "Contenedor Marron (Organico)",
                    "pizza": "Contenedor Marron (Organico)",
                    "donut": "Contenedor Marron (Organico)",
                    "cake": "Contenedor Marron (Organico)",
                    "cardboard": "Contenedor Azul (Carton y papel)",
                    "book": "Contenedor Azul (Papel y carton)",
                    "paper": "Contenedor Azul (Papel y carton)",
                    "person": "No es basura, es un ser humano",
                    "cell phone": "Punto Limpio (Residuos Electronicos)",
                    "tv": "Punto Limpio (Residuos Electronicos)",
                    "laptop": "Punto Limpio (Residuos Electronicos)",
                    "mouse": "Punto Limpio (Residuos Electronicos)",
                    "keyboard": "Punto Limpio (Residuos Electronicos)"
                }
                
                respuesta_final = "Resultados del analisis:\n"
                for obj in resultado:
                    contenedor = contenedores.get(obj.lower(), "Contenedor Gris (No reciclable en general)")
                    respuesta_final += f"- Objeto detectado: **{obj}** -> Debe ir en: {contenedor}\n"
                
                await ctx.send(respuesta_final)

        except Exception as e:
            await ctx.send("Lo siento, ha ocurrido un error durante el proceso de inferencia de la imagen.")
            print(f"Error detallado: {e}")

@bot.command()
async def eco_accion(ctx):
    if len(ctx.message.attachments) == 0:
        await ctx.send("Detector de Eco-Acciones: Debes adjuntar una imagen junto con el comando $eco_accion para verificar tu accion.")
        return

    for attachment in ctx.message.attachments:
        nombre_archivo = attachment.filename
        
        extensiones_validas = ('.png', '.jpg', '.jpeg', '.webp')
        if not nombre_archivo.lower().endswith(extensiones_validas):
            await ctx.send("Formato de archivo incorrecto. Por favor, envia una imagen valida (PNG, JPG, JPEG).")
            continue

        carpeta = "images_eco"
        
        if not os.path.exists(carpeta):
            os.makedirs(carpeta)
            
        ruta_guardado = os.path.join(carpeta, nombre_archivo)
        
        try:
            await attachment.save(ruta_guardado)
            await ctx.send("Analizando la eco-accion...")

            model_path = "model/model.pt"
            labels_path = "model/labels.txt"

            resultado = get_class(model_path=model_path, labels_path=labels_path, image_path=ruta_guardado)

            if not resultado:
                await ctx.send("No se detectaron elementos suficientes en la imagen.")
            elif "Error_Import" in resultado:
                await ctx.send("Error: Para usar la IA necesitas instalar ultralytics.")
            else:
                objetos_minus = [obj.lower() for obj in resultado]
                
                es_movilidad_sostenible = "person" in objetos_minus and "bicycle" in objetos_minus
                es_plantacion = "person" in objetos_minus and ("potted plant" in objetos_minus or "plant" in objetos_minus)
                
                if es_movilidad_sostenible:
                    await ctx.send("Eco-accion validada correctamente: Usar bicileta en lugar de automóviles que utilizan líquidios peligrosos para el medio ambiente. Puntos otorgados.")
                elif es_plantacion:
                    await ctx.send("Eco-accion validada correctamente: Reforestacion o cuidado de plantas detectado. Puntos otorgados.")
                else:
                    detectados_str = ", ".join(resultado)
                    await ctx.send(f"Elementos detectados: {detectados_str}. Lo siento, no se encontró lo necesario para validar una eco-acción (ejemplo: persona + bicicleta o persona + planta).")

        except Exception as e:
            await ctx.send("Lo siento, ha ocurrido un error durante la validacion de la eco-accion.")
            print(f"Error detallado: {e}")

retos = [
    "Eco-Reto: Hoy evita usar bolsas plasticas.",
    "Eco-Reto: Recicla al menos 3 objetos en tu casa.",
    "Eco-Reto: Usa una botella reutilizable hoy.",
    "Eco-Reto: Apaga las luces cuando no las uses.",
    "Eco-Reto: Reutiliza una caja o botella en lugar de tirarla.",
    "Eco-Reto: Separa papel y plastico durante todo el dia."
]

@bot.command()
async def reto(ctx):
    user_id = ctx.author.id
    hoy = datetime.date.today()

    if user_id in reto_usado and reto_usado[user_id] == hoy:
        await ctx.send("Ya reclamaste tu eco-reto hoy. Vuelve manana para uno nuevo.")
        return

    reto_usado[user_id] = hoy

    r = random.choice(retos)
    await ctx.send(r)

@bot.command()
async def basura(ctx):
    await ctx.send("Cuantas bolsas de basura produces al dia? Escribe solo el numero.")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await bot.wait_for('message', timeout=30.0, check=check)
        bolsas = int(msg.content)

        if bolsas <= 2:
            await ctx.send("Genial, produces pocos residuos. Muy bien! Sigue reciclando.")

        elif bolsas <= 5:
            await ctx.send("Oh, produces una cantidad moderada de residuos. Intenta reducir el plastico.")

        else:
            await ctx.send("Wow, produces muchos residuos. Trata de reciclar mas y reutilizar objetos.")

    except:
        await ctx.send("Debes escribir solo un numero.")

bot.run("Token aquí")
