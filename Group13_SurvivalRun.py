
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random

# ----------------- Window & Camera -----------------
camera_pitch = 40
camera_height = 200
camera_distance = 200
fovY = 60
GRID_LENGTH = 300

# Stick player done by Waqar
step = 0.0
stickman_z = 0.0
lane = 0  # -1,0,1
lane_width = 40.0
speed = 2.0
running = False
countdown_active = True
is_jumping = False
jump_height = 0.0
jump_velocity = 0.0
gravity = -0.8
score = 0
high_score = 0
game_over = False


obstacles = []
coins = []
environment_objects = []

countdown = 3
countdown_timer = 0.0
previous_time = None


power_booster = None
booster_active = False
booster_timer = 0.0
last_booster_time = 0.0


traffic_state = 'waiting_first'
traffic_timer = 0.0
game_start_time = None
first_red_delay = 30.0
red_countdown_duration = 3.0
red_duration = 5.0
green_duration = 60.0
paused_for_light = False
traffic_x = -lane_width * 2.5
traffic_y = 0
traffic_pole_height = 100
red_wait_timer = 0.0
green_wait_timer = 0.0

# ----------------- Helpers -----------------
def begin_ortho():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

def end_ortho():
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_small_ui_text(x, y, s):
    begin_ortho()
    glColor3f(1, 1, 1)
    glRasterPos2f(x, y)
    for ch in s:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    end_ortho()

def draw_large_ui_text(x, y, s):
    begin_ortho()
    glColor3f(1, 1, 0)
    glRasterPos2f(x, y)
    for ch in s:
        glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(ch))
    end_ortho()

def draw_cube(w, h, d):
    glPushMatrix()
    glScalef(w, h, d)
    glutSolidCube(1.0)
    glPopMatrix()

def draw_obstacle(x, y, z, width, height, depth):
    glPushMatrix()
    glTranslatef(x, y + 0.5, z)  
    glColor3f(0.8, 0.2, 0.2)
    draw_cube(width, height, depth)
    glPopMatrix()

def draw_coin(x, y, z, radius=5.0):
    quad = gluNewQuadric()
    glPushMatrix()
    glTranslatef(x, y + 0.5, z) 
    glColor3f(1.0, 0.8, 0.0)
    gluSphere(quad, radius, 20, 20)
    glPopMatrix()

def draw_train_car(x, z, length=100.0, height=60.0, width=35.0):
    glPushMatrix()
    glTranslatef(x, height/2, z)
    glColor3f(0.2, 0.2, 0.8)
    draw_cube(width, height, length)
    glPopMatrix()

def draw_stickman():
    global jump_height, step
    y_offset = jump_height + 0.5  
    glPushMatrix()
    glTranslatef(lane * lane_width, y_offset, 0)
    glColor3f(1, 1, 1)
    # Head
    glPushMatrix()
    glTranslatef(0, 80, 0)
    glutSolidSphere(15, 20, 20)
    glPopMatrix()
    # Body
    glPushMatrix()
    glTranslatef(0, 40, 0)
    draw_cube(15, 60, 10)
    glPopMatrix()
    # Arms
    arm_angle = 30 * math.sin(step)
    glPushMatrix()
    glTranslatef(-25, 50, 0)
    glRotatef(arm_angle, 1, 0, 0)
    draw_cube(10, 40, 10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(25, 50, 0)
    glRotatef(-arm_angle, 1, 0, 0)
    draw_cube(10, 40, 10)
    glPopMatrix()
    # Legs
    leg_angle = 30 * math.sin(step)
    glPushMatrix()
    glTranslatef(-10, -10, 0)
    glRotatef(-leg_angle, 1, 0, 0)
    draw_cube(10, 50, 10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(10, -10, 0)
    glRotatef(leg_angle, 1, 0, 0)
    draw_cube(10, 50, 10)
    glPopMatrix()
    glPopMatrix()

def draw_lanes():
    colors = [(0.5, 0, 0), (0.3, 0.3, 0.3), (0, 0, 0.5)]
    lane_positions = [-lane_width, 0, lane_width]
    for i in range(3):
        x = lane_positions[i]
        glBegin(GL_QUADS)
        glColor3f(*colors[i])
        glVertex3f(x - lane_width/2, 0, -GRID_LENGTH)
        glVertex3f(x + lane_width/2, 0, -GRID_LENGTH)
        glVertex3f(x + lane_width/2, 0, GRID_LENGTH)
        glVertex3f(x - lane_width/2, 0, GRID_LENGTH)
        glEnd()

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, 1.25, 0.1, 1000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(0, camera_height, camera_distance, 0, camera_pitch, 0, 0, 1, 0)

def draw_triangle(x, y, z, size=20):
    glPushMatrix()
    glTranslatef(x, y + 0.5, z)  # Slightly raise power booster
    glColor3f(1.0, 0.5, 0.0)
    glBegin(GL_TRIANGLES)
    glVertex3f(0, size, 0)
    glVertex3f(-size, -size, 0)
    glVertex3f(size, -size, 0)
    glEnd()
    glPopMatrix()

# Done by Waqar Game Mechanics
def update_jump(delta_time):
    global jump_height, jump_velocity, is_jumping
    if is_jumping:
        jump_velocity += gravity * delta_time * 60
        jump_height += jump_velocity * delta_time * 60
        if jump_height <= 0:
            jump_height = 0
            jump_velocity = 0
            is_jumping = False

def generate_obstacles():
    global obstacles, coins, environment_objects
    obstacles = [obs for obs in obstacles if obs['z'] < GRID_LENGTH]
    coins = [coin for coin in coins if coin['z'] < GRID_LENGTH]
    environment_objects = [obj for obj in environment_objects if obj['z'] < GRID_LENGTH]
    if random.random() < 0.03 and len(obstacles) < 5:
        lane_choice = random.choice([-1,0,1])
        obstacles.append({'x': lane_choice * lane_width, 'y':0, 'z': -300, 'width':20,'height':40,'depth':10})
    if random.random() < 0.08 and len(coins) < 10:
        lane_choice = random.choice([-1,0,1])
        coins.append({'x': lane_choice * lane_width,'y':50,'z': -300,'radius':5})
    if random.random() < 0.02 and len(environment_objects) < 3:
        side = random.choice([-1,1])
        environment_objects.append({'x': side * (lane_width * 2), 'z': -400,'type':'train'})

def update_power_booster(delta_time, current_time):
    global power_booster, booster_active, booster_timer, last_booster_time
    if not power_booster and not booster_active:
        if current_time - last_booster_time >= 60.0:
            lane_choice = random.choice([-1,0,1])
            power_booster = {'x': lane_choice * lane_width, 'y':50, 'z': -300, 'size':20}
            last_booster_time = current_time
    if power_booster:
        power_booster['z'] += speed * delta_time * 60
    if booster_active:
        booster_timer += delta_time
        if booster_timer >= 45.0:
            booster_active = False
            booster_timer = 0.0

def check_collisions():
    global running, score, game_over, high_score
    global power_booster, booster_active
    player_x = lane * lane_width
    player_y = jump_height + 40
    player_z = 0
    # Obstacles
    for obs in obstacles:
        x_dist = abs(player_x - obs['x'])
        z_dist = abs(player_z - obs['z'])
        if x_dist < 20 and z_dist < 15 and not booster_active and jump_height < obs['height'] +10:
            running = False
            game_over = True
            if score > high_score:
                high_score = score
            return
    # Coins
    for coin in coins[:]:
        x_dist = abs(player_x - coin['x'])
        z_dist = abs(player_z - coin['z'])
        y_dist = abs(player_y - coin['y'])
        if x_dist < 20 and z_dist < 15 and y_dist < 25:
            coins.remove(coin)
            score += 10
    # Booster Done by prity
    if power_booster:
        x_dist = abs(player_x - power_booster['x'])
        z_dist = abs(player_z - power_booster['z'])
        y_dist = abs(player_y - power_booster['y'])
        if x_dist < 20 and z_dist < 15 and y_dist < 30:
            booster_active = True
            booster_timer = 0.0
            power_booster = None

def reset_game():
    global stickman_z, lane, step, running, countdown_active
    global countdown, countdown_timer, obstacles, coins, environment_objects
    global is_jumping, jump_height, jump_velocity, score, game_over
    global traffic_state, traffic_timer, game_start_time, paused_for_light
    global power_booster, booster_active, booster_timer, last_booster_time
    stickman_z = 0.0
    lane = 0
    step = 0.0
    running = False
    countdown_active = True
    countdown = 3
    countdown_timer = 0.0
    obstacles = []
    coins = []
    environment_objects = []
    is_jumping = False
    jump_height = 0.0
    jump_velocity = 0.0
    score = 0
    game_over = False
    # reset traffic
    traffic_state = 'waiting_first'
    traffic_timer = 0.0
    game_start_time = None
    paused_for_light = False
    # reset power booster
    power_booster = None
    booster_active = False
    booster_timer = 0.0
    last_booster_time = 0.0

# Done by prity Traffic Light Drawing
def draw_traffic_light():
    
    glPushMatrix()
    # Pole (thin, short)
    glTranslatef(traffic_x, traffic_pole_height/2, -50)
    glPushMatrix()
    glScalef(3.0, traffic_pole_height, 3.0)
    glColor3f(0.15, 0.15, 0.15)
    glutSolidCube(1.0)
    glPopMatrix()
    # Head with single light
    glPushMatrix()
    glTranslatef(0, traffic_pole_height/2 + 10, 0)
    
    glPushMatrix()
    glScalef(14.0, 22.0, 8.0)
    glTranslatef(0, -0.5, 0)
    glColor3f(0.05, 0.05, 0.05)
    glutSolidCube(1.0)
    glPopMatrix()

    red_active = (traffic_state == 'red' or traffic_state == 'red_countdown')
    green_active = (traffic_state == 'green')
    
    if red_active:
        glPushMatrix()
        glTranslatef(0, 0, 6)
        glColor3f(1.0, 0.0, 0.0)
        glutSolidSphere(7, 20, 20)
        glPopMatrix()
    elif green_active:
        glPushMatrix()
        glTranslatef(0, 0, 6)
        glColor3f(0.0, 1.0, 0.0)
        glutSolidSphere(7, 20, 20)
        glPopMatrix()
    
    glPopMatrix()
    glPopMatrix()

def draw_traffic_countdown_and_messages():
    
    if traffic_state == 'red_countdown':
        remaining = max(0.0, red_countdown_duration - traffic_timer)
        draw_large_ui_text(430, 450, f"RED in {int(math.ceil(remaining))}")
    elif traffic_state == 'red':
        if not paused_for_light:
            draw_large_ui_text(300, 450, "RED! PRESS 'P' TO PAUSE")
        else:
            draw_small_ui_text(10,700, "Paused for red — runway & stickman stopped")
    elif traffic_state == 'green':
        if paused_for_light:
            draw_large_ui_text(350, 450, "GREEN! PRESS 'P' TO RESUME")
        else:
            draw_small_ui_text(10,700, "Green — keep running")

# ----------------- Countdown -----------------
def update_countdown(delta_time):
    global countdown, countdown_timer, countdown_active, running, game_start_time
    if not countdown_active:
        return
    countdown_timer += delta_time
    if countdown_timer >= 1.0:
        countdown -= 1
        countdown_timer = 0.0
    if countdown < 0:
        countdown_active = False
        running = True
        
        if game_start_time is None:
            game_start_time = glutGet(GLUT_ELAPSED_TIME) / 1000.0

def show_countdown_overlay():
    if not countdown_active:
        return
    text = str(countdown) if countdown >0 else "GO!"
    begin_ortho()
    glColor4f(1,1,1,0.9)
    glPushMatrix()
    glRasterPos2f(500,400)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(ch))
    glPopMatrix()
    end_ortho()

#Done by Waqar
def calculate_distance(x, y, z):
    
    camera_pos = [0, camera_height, camera_distance]
    obj_pos = [x, y, z]
    return math.sqrt(sum((camera_pos[i] - obj_pos[i])**2 for i in range(3)))

def draw_scene():
    
    glBegin(GL_QUADS)
    glColor3f(0.5,0.7,1.0)
    glVertex3f(-GRID_LENGTH,200,-GRID_LENGTH)
    glVertex3f(GRID_LENGTH,200,-GRID_LENGTH)
    glVertex3f(GRID_LENGTH,200,GRID_LENGTH)
    glVertex3f(-GRID_LENGTH,200,GRID_LENGTH)
    glEnd()

    # Draw grid lines
    glBegin(GL_LINES)
    glColor3f(0.3,0.3,0.3)
    for i in range(-GRID_LENGTH,GRID_LENGTH+1,20):
        glVertex3f(-GRID_LENGTH,0,i)
        glVertex3f(GRID_LENGTH,0,i)
        glVertex3f(i,0,-GRID_LENGTH)
        glVertex3f(i,0,GRID_LENGTH)
    glEnd()
    
    
    draw_lanes()
    
    
    objects_to_draw = []
    
    # Add obstacles
    for obs in obstacles:
        objects_to_draw.append(("obstacle", obs['x'], obs['y'], obs['z']))
    
    
    for coin in coins:
        objects_to_draw.append(("coin", coin['x'], coin['y'], coin['z']))
    
    
    for obj in environment_objects:
        objects_to_draw.append(("env", obj['x'], 0, obj['z']))
    
    
    if power_booster:
        objects_to_draw.append(("booster", power_booster['x'], power_booster['y'], power_booster['z']))
    
    # Add traffic light
    objects_to_draw.append(("traffic_light", traffic_x, traffic_y, -50))
    
    # Sort objects by distance from camera (farthest first)
    objects_to_draw.sort(key=lambda obj: calculate_distance(obj[1], obj[2], obj[3]), reverse=True)
    
    # Draw objects in sorted order
    for obj_type, x, y, z in objects_to_draw:
        if obj_type == "obstacle":
            for obs in obstacles:
                if obs['x'] == x and obs['y'] == y and obs['z'] == z:
                    draw_obstacle(obs['x'], obs['y'], obs['z'], obs['width'], obs['height'], obs['depth'])
                    break
        elif obj_type == "coin":
            for coin in coins:
                if coin['x'] == x and coin['y'] == y and coin['z'] == z:
                    draw_coin(coin['x'], coin['y'], coin['z'], coin['radius'])
                    break
        elif obj_type == "env":
            for obj in environment_objects:
                if obj['x'] == x and obj['z'] == z:
                    if obj['type'] == 'train':
                        draw_train_car(obj['x'], obj['z'])
                    break
        elif obj_type == "booster":
            if power_booster and power_booster['x'] == x and power_booster['y'] == y and power_booster['z'] == z:
                draw_triangle(power_booster['x'], power_booster['y'], power_booster['z'], power_booster['size'])
        elif obj_type == "traffic_light":
            draw_traffic_light()
    
    
    draw_stickman()

# Done by Waqar
def showScreen():
    global previous_time, step, score, stickman_z
    global game_start_time, traffic_state, traffic_timer, paused_for_light, running, game_over

    current_time = glutGet(GLUT_ELAPSED_TIME)/1000.0
    if previous_time is None:
        previous_time = current_time
    delta_time = current_time - previous_time
    previous_time = current_time

    glClear(GL_COLOR_BUFFER_BIT)
    glViewport(0,0,1000,800)
    setupCamera()

    # Done by Prity
    if game_start_time is None and running and not countdown_active:
        game_start_time = glutGet(GLUT_ELAPSED_TIME)/1000.0

    time_since_game_start = 0.0
    if game_start_time is not None:
        time_since_game_start = current_time - game_start_time

    # Update traffic logic
    if traffic_state == 'waiting_first':
        if time_since_game_start >= first_red_delay:
            traffic_state = 'red_countdown'
            traffic_timer = 0.0
    elif traffic_state == 'red_countdown':
        traffic_timer += delta_time
        if traffic_timer >= red_countdown_duration:
            traffic_state = 'red'
            traffic_timer = 0.0
    elif traffic_state == 'red':
        traffic_timer += delta_time
        if traffic_timer >= red_duration:
            if not paused_for_light:
                running = False
                game_over = True
            else:
                traffic_state = 'green'
                traffic_timer = 0.0
    elif traffic_state == 'green':
        traffic_timer += delta_time
        if traffic_timer >= green_duration:
            traffic_state = 'red_countdown'
            traffic_timer = 0.0
            paused_for_light = False

    # Game updates
    if running and not paused_for_light and not game_over:
        generate_obstacles()
        stickman_z += speed * delta_time * 60
        step += 6.0 * delta_time * (speed*0.15)
        score += speed * delta_time *10
        update_jump(delta_time)
        update_power_booster(delta_time, current_time)
        check_collisions()
        for obs in obstacles:
            obs['z'] += speed*delta_time*60
        for coin in coins:
            coin['z'] += speed*delta_time*60
        for obj in environment_objects:
            obj['z'] += speed*delta_time*60
    else:
        update_countdown(delta_time)

    
    draw_scene()

    # Show traffic messages
    draw_traffic_countdown_and_messages()

    
    if countdown_active:
        show_countdown_overlay()

    
    draw_small_ui_text(10,770,f"Speed: {speed:.1f}  |  Score: {int(score)}  |  Distance: {int(stickman_z)}")
    draw_small_ui_text(10,745,"R: Start  S: Stop  Space: Jump  +/-: Speed  ←/→: Lane  PgUp/PgDn: Pitch")
    draw_small_ui_text(10,725,"P: Pause/Resume for traffic light events")

    # Done by Prity SAFEGUARD 
    if booster_active:
        draw_small_ui_text(10,705,"SAFEGUARD MODE ACTIVE")

    if paused_for_light:
        draw_small_ui_text(10,685,"Paused for RED — runway & stickman frozen (no collisions)")

    if game_over:
        draw_large_ui_text(400,400,"GAME OVER")
        draw_small_ui_text(420,370,f"Final Score: {int(score)}")
        draw_small_ui_text(420,350,"Press R to restart")

    glutSwapBuffers()

# ----------------- Input -----------------
def keyboard(key,x,y):
    global countdown_active, countdown, countdown_timer, running, speed
    global is_jumping, jump_velocity, game_over, paused_for_light, traffic_state, traffic_timer, game_start_time

    if game_over and key in (b'r',b'R'):
        reset_game()
        return

    if key in (b'r',b'R'):
        if not countdown_active and not running:
            countdown_active = True
            countdown = 3
            countdown_timer = 0.0
    elif key in (b's',b'S'):
        running = False
    elif key in (b'+',b'='):
        speed = min(10.0,speed+0.2)
    elif key == b'-':
        speed = max(0.1,speed-0.2)
    elif key == b' ' and running and not is_jumping and not game_over:
        is_jumping = True
        jump_velocity = 25.0
    elif key in (b'p', b'P'):
        if traffic_state == 'red' and not paused_for_light and not game_over:
            paused_for_light = True
            running = False
            return
        if traffic_state == 'green' and paused_for_light and not game_over:
            paused_for_light = False
            running = True
            return

def special_input(key,x,y):
    global lane, camera_pitch
    if key == GLUT_KEY_LEFT and lane > -1 and not game_over:
        lane -=1
    elif key == GLUT_KEY_RIGHT and lane < 1 and not game_over:
        lane +=1
    elif key == GLUT_KEY_PAGE_UP:
        camera_pitch += 2
    elif key == GLUT_KEY_PAGE_DOWN:
        camera_pitch -= 2


def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(1000,800)
    glutInitWindowPosition(50,50)
    glutCreateWindow(b"dourao bhai")
    glutDisplayFunc(showScreen)
    glutIdleFunc(showScreen)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_input)
    glutMainLoop()

if __name__ == "__main__":
    main()
