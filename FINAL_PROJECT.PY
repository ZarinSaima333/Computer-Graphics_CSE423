import random
import sys
import math
import time
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from math import cos, sin, radians

in_menu = True  # Global variable to track whether we're in the menu or the game

falling_ball_counter = 0

# Global variable to store the start time
start_time = time.time()
game_over_flag = False  # Flag to check if the game is over


# Tank properties
tank_x = 400
tank_y = 300
tank_speed = 10

# Ball properties
active_balls = []
falling_balls = []

# Score
score = 0

# Lives
tank_lives = 3
is_exploding = False
explosion_start_time = 0

# New global variables
last_explosion_time = 0  # Track the time of the last explosion
EXPLOSION_COOLDOWN = 3000

# Cannon properties
cannon_angle = 0

# Utility function to draw points
def draw_points(points, size=1):
    glPointSize(size)
    glBegin(GL_POINTS)
    for (x, y) in points:
        glVertex2f(x, y)
    glEnd()
def midpoint_line(x0, y0, x1, y1):
    points = []
    dx = x1 - x0
    dy = y1 - y0
    d = 2 * dy - dx  # Initial decision parameter
    x, y = x0, y0

    points.append((x, y))  # Start point

    while x < x1:
        if d > 0:
            y += 1
            d += 2 * (dy - dx)
        else:
            d += 2 * dy
        x += 1
        points.append((x, y))

    return points

def draw_midline(x0, y0, x1, y1, size=1):
    points = midpoint_line(x0, y0, x1, y1)
    glPointSize(size)
    glBegin(GL_POINTS)
    for x, y in points:
        glVertex2f(x, y)
    glEnd()

# Generate points for a circle

# mid_point_algo banabo #offset
def mid_point_circle_alg(radius, x_center, y_center):
    points = []
    
    # Initial point
    x, y = 0, radius
    p = 1 - radius  # Initial decision parameter

    # Generate points for one octant
    while x <= y:
        # Add the points in all eight octants
        points.extend([
            (x_center + x, y_center + y),
            (x_center - x, y_center + y),
            (x_center + x, y_center - y),
            (x_center - x, y_center - y),
            (x_center + y, y_center + x),
            (x_center - y, y_center + x),
            (x_center + y, y_center - x),
            (x_center - y, y_center - x),
        ])
        
        x += 1
        if p < 0:
            p += 2 * x + 1
        else:
            y -= 1
            p += 2 * (x - y) + 1

    return points


# Tank drawing
def draw_tank():
    glPushMatrix()
    glTranslatef(tank_x, tank_y, 0)

    # Tank body
    body_points = [(x, y) for x in range(-25, 26) for y in range(-15, 16)]
    glColor3f(0.0, 0.6, 0.2)
    draw_points(body_points, size=2)

    # Turret base
    turret_points = mid_point_circle_alg(8, 0, 5)
    glColor3f(0.0, 0.5, 0.0)
    draw_points(turret_points, size=2)

    # Cannon
    glPushMatrix()
    glTranslatef(0, 10, 0)
    glRotatef(cannon_angle, 0, 0, 1)
    cannon_points = [(x, y) for x in range(0, 36) for y in range(-3, 4)]
    glColor3f(0.0, 0.4, 0.0)
    draw_points(cannon_points, size=2)
    glPopMatrix()

    # Wheels
    glColor3f(0.2, 0.2, 0.2)
    wheel_positions = [
        (-20, -20), (-10, -20), (0, -20), (10, -20), (20, -20)
    ]
    for wx, wy in wheel_positions:
        wheel_points = mid_point_circle_alg(7, wx, wy)
        draw_points(wheel_points, size=2)

    # Tracks
    track_points = [(x, y) for x in range(-27, 28) for y in range(-22, -18)]
    glColor3f(0.1, 0.1, 0.1)
    draw_points(track_points, size=1)

    glPopMatrix()

# Ball drawing
def draw_ball(ball):

    if ball['size'] == 'small':
        ball_points = mid_point_circle_alg(5, ball['x'], ball['y'])
    else:
        ball_points = mid_point_circle_alg(15, ball['x'], ball['y']) 

    if ball in active_balls:  # Check if the ball is an active tank bullet
        glColor3f(1.0, 1.0, 0.0)  # Yellow color for tank bullets
    else:
        glColor3f(0.0, 0.0, 1.0) if ball['size'] == 'small' else glColor3f(1.0, 0.0, 0.0) #red= small, blue= big
    draw_points(ball_points, size=2) 

# Explosion effect
def draw_explosion(center_x, center_y, max_radius, steps=30):
    """Draw an explosion with randomized, expanding fragments."""
    for step in range(steps):
        # Generate random angle and radius for each fragment
        for _ in range(20):  # Number of fragments in each step
            angle = random.uniform(0, 2 * math.pi)
            radius = random.uniform(0, max_radius * (step / steps))  # Random radius within expanding range
            x_offset = math.cos(angle) * radius
            y_offset = math.sin(angle) * radius

            # Generate random colors for each fragment (for a fiery look)
            r = random.uniform(0.8, 1.0)  # Red component (explosive look)
            g = random.uniform(0.4, 0.6)  # Green component (smokey effect)
            b = random.uniform(0, 0.3)    # Blue component (for fire-like color)
            alpha = random.uniform(0.5, 1.0)  # Random alpha for fading effect

            glColor4f(r, g, b, alpha)  # Set color with transparency
            glBegin(GL_POINTS)  # Use points to simulate small fragments
            glVertex2f(center_x + x_offset, center_y + y_offset)  # Fragment position
            glEnd()


TANK_RADIUS = 20  # Approximate the tank as a circle
BALL_RADIUS = 10  # Approximate the ball as a circle

def detect_tank_collision():
    global tank_lives, is_exploding, explosion_start_time, last_explosion_time

    current_time = glutGet(GLUT_ELAPSED_TIME)

    # Check if explosion cooldown is active
    if is_exploding or (current_time - last_explosion_time < EXPLOSION_COOLDOWN):
        return  # Skip if still exploding or cooldown is active
    
    for ball in falling_balls[:]:  # Iterate over a copy of falling balls

        if ball.get('exploded', False):
            continue

        distance = ((tank_x - ball['x'])**2 + (tank_y - ball['y'])**2) ** 0.5

        if distance < (TANK_RADIUS + BALL_RADIUS):  # Collision threshold
            ball['exploded'] = True
            falling_balls.remove(ball)  # Remove the falling ball
            tank_lives -= 1  # Reduce tank life
            is_exploding = True
            explosion_start_time = current_time  # Record explosion start time
            last_explosion_time = current_time  # Update last explosion time
            
            print("Explosion triggered!")
            if tank_lives <= 0:
                print("Game Over!")  # Replace with game over logic
                return

            break  # Exit loop on collision
def update_explosion():
    """
    Update explosion state. End the explosion after 3 seconds.
    """
    global is_exploding, explosion_start_time

    if is_exploding:
        current_time = glutGet(GLUT_ELAPSED_TIME)  # Get current time in milliseconds
        if current_time - explosion_start_time > 3000:  # Explosion lasts 3 seconds
            is_exploding = False  # Reset explosion state
# Utility function to draw text
def draw_text(string, x, y, font_size=18, color=(1.0, 1.0, 1.0)):
    # Set text color to green
    glColor3f(*color)
    glRasterPos2f(x, y)
    for char in string:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))  # You can change the font here for bigger size


def set_blue_background():
    # Set the background color to blue (RGB values)
    glClearColor(0.0, 1.0, 1.0, 0.0)  # (Red, Green, Blue, Alpha)
    glClear(GL_COLOR_BUFFER_BIT)  # Clear the screen and apply the color

# def render():
#     #set_blue_background()  # Set the background color to blue
#     # Your other rendering code goes here (drawing objects, etc.)
#     if tank_lives <= 0:  # If the tank has no lives left
#         draw_text("Game Over! You're out of lives.", 300, 300)
#         draw_text("Press 'R' to restart.", 300, 270)
#     else:
#         # Your other rendering code goes here (drawing objects, etc.)
#         for ball in falling_balls:
#             draw_ball(ball)  # Draw falling balls
#         for ball in active_balls:
#             draw_ball(ball)  # Draw active balls
#         draw_tank()
#         if is_exploding:
#             draw_explosion(tank_x, tank_y, 50)  # Draw explosion effect
#     glutSwapBuffers()

# Display function
# def display():
#     global start_time, game_over_flag
#     glClear(GL_COLOR_BUFFER_BIT)
#     #set_blue_background()
#     elapsed_time = time.time() - start_time
#     draw_text(f"Score: {score}", 650, 570)
#     draw_text(f"Lives: {tank_lives}", 650, 550)

#     # Calculate the remaining time (60 seconds - elapsed time)
#     remaining_time = max(0, 60 - int(elapsed_time))  # Ensure time doesn't go negative

#     # Display the countdown timer in the top-right corner
#     draw_text(f"Time Left: {remaining_time} sec", 650, 530)  # Modify this position for top-right
    
#     if tank_lives <= 0:  # If the tank has no lives left
#         draw_text("Game Over! You're out of lives.", 300, 300)
#         draw_text("Press 'R' to restart.", 300, 270)
#         game_over_flag = True
#     elif remaining_time == 0 and score<=0:
#         draw_text("Time's up! Game Over.Your score is: {score}", 300, 300)
#         draw_text("Press 'R' to restart.", 300,)
#         game_over_flag = True

#     elif remaining_time == 0 and score>0:
#         draw_text(f"You Win. Your score is: {score}", 300, 300)
#         draw_text("Press 'R' to restart.", 300,)
#         game_over_flag = True
#     else:
#         for ball in falling_balls:
#             draw_ball(ball)  # Draw falling balls
#         for ball in active_balls:
#             draw_ball(ball)  # Draw active balls
#         draw_tank()
#         if is_exploding:
#             draw_explosion(tank_x, tank_y, 50)  # Draw explosion effect
        
    
#     glutSwapBuffers()
def draw_menu():
    # Draw "Save Your Tank" with larger font and green color
    draw_text("Save Your Tank", 340, 450, font_size=50, color=(0.0, 1.0, 0.0))
    draw_text("Play", 390, 215)
    
    # Draw button edges with midline
    # Further adjusted midline y-coordinates to move them more below the tank
    draw_midline(330, 240, 500, 240) # Top edge (moved down to y=320)
    #draw_midline(330, 240, 330, 200)  # Left edge (moved down to y=380)
    #draw_midline(500, 320, 500, 380)  # Right edge (moved down to y=380)
    draw_midline(330, 200, 500, 200)  # Bottom edge (moved down to y=380)
    draw_tank()
    draw_explosion(400,400,60)

def mouse_click(button, state, x, y):
    global in_menu
    # Convert mouse click y-coordinate to OpenGL's coordinate system
    screen_height = glutGet(GLUT_WINDOW_HEIGHT)
    y = screen_height - y  # Convert y-coordinate to OpenGL's bottom-left origin system

    # Check if click is inside the play button
    if in_menu and 330 <= x <= 500 and 200 <= y <= 240:
        print("Starting the game...")
        in_menu = False  # Switch to the game state
    elif in_menu == False and 10 <= x <= 40 and 200 <= y <= 600:
        print("Starting the menu...")
        in_menu = True 
        restart_game()
def display():
    global start_time, game_over_flag
    glClear(GL_COLOR_BUFFER_BIT)
    if in_menu:
        draw_menu()
    else:
        elapsed_time = time.time() - start_time
        draw_text(f"Score: {score}", 650, 570)
        draw_text(f"Lives: {tank_lives}", 650, 550)
        draw_text(f"X", 30, 570)
        # Calculate the remaining time (60 seconds - elapsed time)
        remaining_time = max(0, 60 - int(elapsed_time))  # Ensure time doesn't go negative

        # Display the countdown timer in the top-right corner
        draw_text(f"Time Left: {remaining_time} sec", 650, 530)  # Modify this position for top-right

        if tank_lives <= 0:  # If the tank has no lives left
            draw_text("Game Over! You're out of lives.", 300, 300)
            draw_text("Press 'R' to restart.", 300, 270)
        elif remaining_time == 0 and score <= 0:
            draw_text("Time's up! Game Over.", 300, 300)
            draw_text("Press 'R' to restart.", 300, 270)
        elif remaining_time == 0 and score > 0:
            draw_text(f"You Win. Your score is: {score}", 300, 300)
            draw_text("Press 'R' to restart.", 300, 270)
        else:
            # Update game elements: Balls, Tank, etc.
            for ball in falling_balls:
                draw_ball(ball)  # Draw falling balls
            for ball in active_balls:
                draw_ball(ball)  # Draw active balls
            draw_tank()
            
            if is_exploding:
                draw_explosion(tank_x, tank_y, 50)  # Draw explosion effect

    glutSwapBuffers()



# Move tank
def move_tank(direction):
    global tank_x, tank_y
    if direction == 'up' and tank_y + 10 < 600:
        tank_y += tank_speed
    elif direction == 'down' and tank_y - 10 > 0:
        tank_y -= tank_speed
    elif direction == 'left' and tank_x - 20 > 0:
        tank_x -= tank_speed
    elif direction == 'right' and tank_x + 20 < 800:
        tank_x += tank_speed
# Add a function to restart the game


def restart_game():
    global tank_x, tank_y, tank_lives, score, active_balls, falling_balls, is_exploding, start_time
    tank_x, tank_y = 400, 300  # Reset tank position
    tank_lives = 3  # Reset lives
    score = 0  # Reset score
    active_balls = []  # Clear active balls
    falling_balls = []  # Clear falling balls
    is_exploding = False  # Reset explosion state
    start_time = time.time()  # Reset the start time



# Keyboard controls
def keyboard(key, x, y): #tank movement and shoot
    if key == b'w':
        move_tank('up')
    elif key == b's':
        move_tank('down')
    elif key == b'a':
        move_tank('left')
    elif key == b'd':
        move_tank('right')
    elif key == b' ':
        shoot_ball()  # This will shoot the ball when the spacebar is pressed
    elif key == b'\x1b':
        sys.exit()
    elif key == b'r' or key == b'R':  # Restart the game when 'R' is pressed
        restart_game()


# Special keys for rotation
def special_keys(key, x, y): # Special keys for rotation
    global cannon_angle
    if key == GLUT_KEY_RIGHT:
        cannon_angle -= 5
    elif key == GLUT_KEY_LEFT:
        cannon_angle += 5
    glutPostRedisplay()



# Shoot ball
def shoot_ball():
    global active_balls
    rad_angle = radians(cannon_angle)
    #bullet speed
    dx = cos(rad_angle) * 3  # Set the x velocity component based on the cannon angle 
    dy = sin(rad_angle) * 3  # Set the y velocity component based on the cannon angle
    new_ball = {'x': tank_x, 'y': tank_y, 'dx': dx, 'dy': dy, 'size': 'small'}  # Add size here
    active_balls.append(new_ball)  # Add the new ball to the active balls list



# Update balls
# Update tank bullets and detect collisions
def update_tank_bullet():
    global active_balls, falling_balls, score
    for ball in active_balls:
        ball['x'] += ball['dx']
        ball['y'] += ball['dy']

    # Ball collision detection
    # Ball collision detection
    for falling_ball in falling_balls[:]:  # Iterate over a copy of the list
        for ball in active_balls[:]:  # Iterate over a copy of active balls
            # Calculate distance
            distance = ((falling_ball['x'] - ball['x'])**2 + (falling_ball['y'] - ball['y'])**2) ** 0.5
            
            # Adjust collision threshold based on ball sizes
            collision_threshold = 5 + (5 if falling_ball['size'] == 'small' else 15)  # Bullet radius + Falling ball radius
            
            if distance < collision_threshold:  # Check if the balls collide
                active_balls.remove(ball)  # Remove the bullet
                falling_balls.remove(falling_ball)  # Remove the falling ball
                score += falling_ball['points']  # Update score
                break  # Exit inner loop when collision occurs


    # Remove out-of-bounds balls
    falling_balls = [ball for ball in falling_balls if 0 <= ball['x'] <= 800 and 0 <= ball['y'] <= 600]
    active_balls = [ball for ball in active_balls if 0 <= ball['x'] <= 800 and 0 <= ball['y'] <= 600]


# Create falling balls
def create_falling_ball():
    ball_type = random.choice(['small', 'big'])
    ball_size = 5 if ball_type == 'big' else 3 #kaaj hoy nai.
    ball_points = 5 if ball_type == 'small' else -10
    direction = random.choice(['top_to_bottom', 'bottom_to_top', 'left_to_right', 'right_to_left'])

    if direction == 'top_to_bottom':
        dx, dy = 0, random.uniform(-0.5, -1)
        start_x, start_y = random.randint(0, 800), 600
    elif direction == 'bottom_to_top':
        dx, dy = 0, random.uniform(0.5, 1)
        start_x, start_y = random.randint(0, 800), 0
    elif direction == 'left_to_right':
        dx, dy = random.uniform(0.5, 1), 0
        start_x, start_y = 0, random.randint(0, 600)
    elif direction == 'right_to_left':
        dx, dy = random.uniform(-0.5, -1), 0
        start_x, start_y = 800, random.randint(0, 600)

    ball = {
        'x': start_x,
        'y': start_y,
        'dx': dx,
        'dy': dy,
        'size': ball_type,
        'points': ball_points
    }
    falling_balls.append(ball)

# Update falling balls
def update_falling_balls():
    for ball in falling_balls:
        ball['x'] += ball['dx']
        ball['y'] += ball['dy']


# def render():
#     #set_blue_background()  # Set the background color to blue
#     # Your other rendering code goes here (drawing objects, etc.)
#     if tank_lives <= 0:  # If the tank has no lives left
#         draw_text("Game Over! You're out of lives.", 300, 300)
#         draw_text("Press 'R' to restart.", 300, 270)
#     else:
#         # Your other rendering code goes here (drawing objects, etc.)
#         for ball in falling_balls:
#             draw_ball(ball)  # Draw falling balls
#         for ball in active_balls:
#             draw_ball(ball)  # Draw active balls
#         draw_tank()
#         if is_exploding:
#             draw_explosion(tank_x, tank_y, 50)  # Draw explosion effect
#     glutSwapBuffers()

# Display function
# def display():
#     global start_time, game_over_flag
#     glClear(GL_COLOR_BUFFER_BIT)
#     #set_blue_background()
#     elapsed_time = time.time() - start_time
#     draw_text(f"Score: {score}", 650, 570)
#     draw_text(f"Lives: {tank_lives}", 650, 550)

#     # Calculate the remaining time (60 seconds - elapsed time)
#     remaining_time = max(0, 60 - int(elapsed_time))  # Ensure time doesn't go negative

#     # Display the countdown timer in the top-right corner
#     draw_text(f"Time Left: {remaining_time} sec", 650, 530)  # Modify this position for top-right
    
#     if tank_lives <= 0:  # If the tank has no lives left
#         draw_text("Game Over! You're out of lives.", 300, 300)
#         draw_text("Press 'R' to restart.", 300, 270)
#         game_over_flag = True
#     elif remaining_time == 0 and score<=0:
#         draw_text("Time's up! Game Over.Your score is: {score}", 300, 300)
#         draw_text("Press 'R' to restart.", 300,)
#         game_over_flag = True

#     elif remaining_time == 0 and score>0:
#         draw_text(f"You Win. Your score is: {score}", 300, 300)
#         draw_text("Press 'R' to restart.", 300,)
#         game_over_flag = True
#     else:
#         for ball in falling_balls:
#             draw_ball(ball)  # Draw falling balls
#         for ball in active_balls:
#             draw_ball(ball)  # Draw active balls
#         draw_tank()
#         if is_exploding:
#             draw_explosion(tank_x, tank_y, 50)  # Draw explosion effect
        
    
#     glutSwapBuffers()
# Idle function


def idle():
    global is_exploding, explosion_start_time
    global falling_ball_counter
    falling_ball_counter += 1

    # Create a new falling ball every 30 cycles (adjust as needed)
    if falling_ball_counter >= 60:  
        create_falling_ball()
        falling_ball_counter = 0 # Generate new falling ball , norbe na charside e create hoye thakbe

    update_tank_bullet()#gulir ball 
    update_falling_balls() #move korabe falling balls

    detect_tank_collision() #tank er collision check korbe

    if is_exploding:
        current_time = glutGet(GLUT_ELAPSED_TIME)
        if current_time - explosion_start_time >= 3000:  # 3 seconds
            is_exploding = False  # End explosion effect

    glutPostRedisplay()

# Initialization
def init():
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glColor3f(1.0, 1.0, 1.0)
    glOrtho(0, 800, 0, 600, -1, 1)



# Main function
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(800, 600)
    glutCreateWindow(b'Tank Game')
    init()
    glutDisplayFunc(display)
    glutIdleFunc(idle)
    glutMouseFunc(mouse_click)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_keys)
    glutMainLoop()

if __name__ == '__main__':
    main()
