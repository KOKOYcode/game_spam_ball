import math
import random
from turtle import *

# Setup Layar
screen = Screen()
screen.bgcolor("black")
screen.setup(width=800, height=600)
screen.tracer(0)  

def hearta(k):
    return 15 * math.sin(k)**3

def heartb(k):
    return 12 * math.cos(k) - 5 * math.cos(2 * k) - math.cos(3 * k) - math.cos(4 * k)


def small_heart_x(t, scale):
    return scale * (16 * math.sin(t)**3)

def small_heart_y(t, scale):
    return scale * (13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))


current_heart_progress = 0
MAX_HEART_STEPS = 350
HEART_GROWTH_SPEED = 3  
heart_finished = False


heart_drawer = Turtle()
heart_drawer.hideturtle()
heart_drawer.speed(0)


text_writer = Turtle()
text_writer.hideturtle()
text_writer.penup()


falling_hearts = []
num_falling_hearts = 15 
for _ in range(num_falling_hearts):
    falling_hearts.append({
        "x": random.randint(-380, 380),
        "y": random.randint(-300, 300),
        "speed": random.uniform(1, 2),
        "size": random.uniform(0.6, 1.0) 
    })

# Turtle khusus untuk menggambar latar belakang hati yang jatuh
falling_drawer = Turtle()
falling_drawer.hideturtle()
falling_drawer.speed(0)
falling_drawer.penup()


def animate():
    global current_heart_progress, heart_finished

    
    falling_drawer.clear()

    
    if not heart_finished:
        for _ in range(HEART_GROWTH_SPEED):
            if current_heart_progress < MAX_HEART_STEPS:
                i = current_heart_progress
                heart_drawer.goto(hearta(i) * 15, heartb(i) * 15)
                heart_drawer.color("purple")
                heart_drawer.goto(0, 0)
                current_heart_progress += 1
            else:
                heart_finished = True
                break

    
    if heart_finished:
        text_writer.color("white")
        text_writer.goto(0, -10)
        text_writer.write("I LOVE TEL-U", align="center", font=("Arial", 24, "bold"))

     
    for h in falling_hearts:
        h["y"] -= h["speed"]
        
        
        if h["y"] < -320:
            h["y"] = 320
            h["x"] = random.randint(-380, 380)
            h["speed"] = random.uniform(1, 2)
        
        
        falling_drawer.color("violet")
        falling_drawer.penup()
        
        falling_drawer.begin_fill()
        
        steps = 20
        for j in range(steps + 1):
            t = j * (2 * math.pi / steps)
            hx = h["x"] + small_heart_x(t, h["size"])
            hy = h["y"] + small_heart_y(t, h["size"])
            if j == 0:
                falling_drawer.goto(hx, hy)
                falling_drawer.pendown()
            else:
                falling_drawer.goto(hx, hy)
        falling_drawer.end_fill()
        falling_drawer.penup()

    screen.update()  
    
    
    screen.ontimer(animate, 20)

animate()

screen.exitonclick()