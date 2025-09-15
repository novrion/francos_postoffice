import pygame
import sys
import random
import math

def time_str(time_int: int):
    if time_int < 0:
        raise ValueError("Invalid time_int arg in time_str(). Should be an integer >= 0.")
    for i in range(time_int // (24 * 60)):
        time_int -= 24 * 60
    hours = time_int // 60
    minutes = time_int % 60
    formatted_minutes = minutes if minutes >= 10 else f"0{minutes}"
    return f"{hours}:{minutes}"

def time_int(time_str: str):
    parts = time_str.strip().split(':')
    if len(parts) != 2:
        raise ValueError("Invalid time_str arg in time_int(). Should be formatted xx:yy (0 <= xx <= 23, 0 <= yy <= 59)")
    try:
        hour = int(parts[0])
        minutes = int(parts[1])
        if not ((0 <= hour <= 23) and (0 <= minutes <= 59)):
            raise ValueError()
        return hour * 60 + minutes
    except ValueError as err:
        raise ValueError("Invalid time_str arg in time_int(). Could not convert xx (hours) and yy (minutes) of 'xx:yy' to integers.")

class Customer:
    def __init__(self, id, current_time):
        self.id = id
        self.n_tasks = self.randomise_n_tasks()
        self.entry_time = current_time
        self.exit_time = None
        self.wait_time = 0

    def randomise_n_tasks(self):
        ret = 1
        while True:
            if random.random() >= 0.5:
                ret += 1
            else:
                return ret

    def set_exit_time(self, current_time, minutes_to_complete_task):
        self.exit_time = current_time + minutes_to_complete_task * self.n_tasks
        self.wait_time = self.exit_time - self.entry_time

class PostOffice:
    def __init__(self):
        self.queue = []
        self.current_time = 0
        self.customer_count = 0
        self.total_customer_wait_time = 0
        
        self.last_robbery_time = None
        self.last_robbery_succeeded = None

        # Parameters
        self.open = time_int("09:00")
        self.close = time_int("18:00")
        self.customer_spawn_probability = 0.2
        self.minutes_to_complete_task = 2
        self.robbery_probability = 0.001
        self.robbery_success_rate = 0.3
        self.robbery_kill_probability = 0.5
        self.robbery_customer_spawn_probability_boost = 0.3
        self.robbery_customer_spawn_probability_drop = 0.15
        self.robbery_customer_spawn_probability_adjustment_coefficient = 10

    def should_do_robbery(self):
        return random.random() <= self.robbery_probability

    def should_spawn_customer(self):
        if self.current_time >= self.close:
            return False
        
        spawn_rate = self.customer_spawn_probability
        if self.last_robbery_time:
            time_diff = self.current_time - self.last_robbery_time
            probability_adjustment = -self.robbery_customer_spawn_probability_drop if self.last_robbery_succeeded else self.robbery_customer_spawn_probability_boost
            spawn_rate = self.customer_spawn_probability + probability_adjustment * pow(math.e, -time_diff/self.robbery_customer_spawn_probability_adjustment_coefficient)

        return random.random() <= spawn_rate

    def simulate_robbery(self, gui):

        # Calculate how many customers die
        # and adjust total waiting time before clearing the queue
        n_kills = 0
        for customer in self.queue:
            self.total_customer_wait_time += self.current_time - customer.entry_time
            if random.random() <= self.robbery_kill_probability:
                n_kills += 1
        self.queue.clear()

        gui.log(f"{time_str(self.current_time)} A robber has entered the post office!")
        gui.log(f"The queue has dispersed and {n_kills} customers have been killed!")

        # Robbery either succeeds or fails
        if random.random() <= self.robbery_success_rate:
            gui.log("Madame Franco, who has a black belt in karate, tries to fight off the robbers, but fails.")
            self.last_robbery_succeeded = True
        else:
            gui.log("Madame Franco, who has a black belt in karate, tries to fight off the robbers, and succeeds!")
            self.last_robbery_succeeded = False

        self.last_robbery_time = self.current_time

    def simulate(self, gui):

        nothing_happened = True
        while nothing_happened:

            # Show end of simulation statistics if past closing time and queue empty
            if self.current_time > self.close and not self.queue:
                gui.show_statistics()
                return

            # Post office opens
            if self.current_time == self.open:
                nothing_happened = False
                gui.log(f"{time_str(self.current_time)} The post office opens")

            # Post office closes
            if self.current_time == self.close:
                nothing_happened = False
                gui.log(f"{time_str(self.current_time)} The post office closes")

            # Robbery
            if self.should_do_robbery():
                self.simulate_robbery(gui)
                self.current_time += 1
                return

            # New customer
            if self.should_spawn_customer():
                nothing_happened = False

                self.customer_count += 1
                new_customer = Customer(self.customer_count, self.current_time)
                if not self.queue:
                    new_customer.set_exit_time(self.current_time, self.minutes_to_complete_task)
                self.queue.append(new_customer)

                if len(self.queue) == 1:
                    gui.log(f"{time_str(self.current_time)} Customer {new_customer.id} enters the post office and is served immediately.")
                else:
                    gui.log(f"{time_str(self.current_time)} Customer {new_customer.id} enters the post office and stands in line as no. {len(self.queue)}")

            # Customer leaves
            if self.queue and self.queue[0].exit_time == self.current_time:
                nothing_happened = False

                completed_customer = self.queue.pop(0)
                self.total_customer_wait_time += completed_customer.wait_time
                if self.queue:
                    gui.log(f"{time_str(self.current_time)} Customer {completed_customer.id} leaves and customer {self.queue[0].id} is served")
                    self.queue[0].set_exit_time(self.current_time, self.minutes_to_complete_task)
                else:
                    gui.log(f"{time_str(self.current_time)} Customer {completed_customer.id} leaves")

            self.current_time += 1

class InputBox:
    def __init__(self, x, y, w, h, font, bg_colour, text_colour):
        self.rect = pygame.Rect(x, y, w, h)
        self.rect_outline = pygame.Rect(x-2, y-2, w+4, h+4)
        self.bg_colour = bg_colour
        self.text_colour = text_colour
        self.font = font
        self.input_text = ""
        self.taking_input = False

    def hovering(self, mouse_x, mouse_y):
        return self.rect.collidepoint(mouse_x, mouse_y)

    def blit(self, screen):
        # Background and outline
        pygame.draw.rect(screen, self.text_colour, self.rect_outline)
        pygame.draw.rect(screen, self.bg_colour, self.rect)

        # Text
        text = self.font.render(self.input_text, False, self.text_colour)
        screen.blit(text, self.rect)

class GUI:
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)

    def __init__(self, width, height):
        pygame.init()
        pygame.display.set_caption("Franco's Post Office")

        self.width = width
        self.height = height

        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()

        self.font_IBM_2y = pygame.font.Font("assets/fonts/Mx437_IBM_CGA-2y.ttf", 16)
        self.font_IBM = pygame.font.Font("assets/fonts/Mx437_IBM_CGA.ttf", 16)

        self.bg0 = pygame.image.load("assets/backgrounds/bg0.png")
        self.bg0_pressed = pygame.image.load("assets/backgrounds/bg0_pressed.png")
        self.bg1 = pygame.image.load("assets/backgrounds/bg1.png")
        self.bg1_hover = pygame.image.load("assets/backgrounds/bg1_hover.png")
        self.bg1_clicked = pygame.image.load("assets/backgrounds/bg1_clicked.png")
        self.bg2 = pygame.image.load("assets/backgrounds/bg2.png")
        self.bg2_pressed = pygame.image.load("assets/backgrounds/bg2_pressed.png")

        # Stores all Rects and input boxes to blit to the current screen
        self.rects = {}
        self.input_boxes = []

        # Game stage
        self.stage = 0

    def set_bg(self, background):
        self.screen.blit(background, (0, 0))

    def log(self, a: str):
        key = "logs"

        # Check if no logs yet
        logs_empty = not (key in self.rects.keys())

        # Append new Rect to GUI Rect dictionary
        x = 240
        y = 585
        text = self.font_IBM_2y.render(a, False, self.BLACK)
        text_rect = text.get_rect()
        text_rect.x = 240
        text_rect.y = 585
        if logs_empty:
            self.rects[key] = [(text, text_rect)]
        else:
            self.rects[key].append((text, text_rect))

        # Only keep the 10 most recent logs
        if not logs_empty and len(self.rects[key]) > 10:
            self.rects[key].pop(0)
        

    def blit_logs(self):
        key = "logs"
        if key in self.rects.keys():
            log_count = 0
            for log in self.rects[key]:
                text = log[0]
                rect = log[1]
                rect.y = 585 + rect.h * log_count
                self.screen.blit(text, rect)
                log_count += 1

    def clicked_play_button(self, mouse_x, mouse_y, left_clicked):
        # Mouse on button?
        button_rect = pygame.Rect((958, 677), (195, 67))
        hovering = button_rect.collidepoin((mouse_x, mouse_y))

        if hovering and left_clicked:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            self.set_bg(self.bg1_clicked) 
            return True

        elif hovering:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            self.set_bg(self.bg1_hover)

        else:
            if pygame.mouse.get_cursor() == pygame.SYSTEM_CURSOR_HAND:
                print("True")
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            self.set_bg(self.bg1)

        return False

    def blit_how_to(self):
        key = "how_to"

        # Rects not generated yet
        if not key in self.rects.keys():

            # How to title
            title_text = self.font_IBM.render("How To Play", False, self.BLACK)
            title_text_rect = title_text.get_rect()
            title_text_rect.x = 70
            title_text_rect.y = 60
            self.rects[key] = [(title_text, title_text_rect)]

            # How to instructions
            raw_text = "Franco's Post Office simulates Madame Franco's post office. Every minute the store is open a customer may enter. Every customer has a randomised number of tasks that he or she needs to complete. If there are no other customers in the store Franco will get to work on the new customer's tasks right away. Otherwise the customer enters the queue. When Franco has completed all of a customer's tasks the customer leaves. Rarely the post office is robbed. Franco usually manages to fight off the robbers with her black belt in karate. Then the post office gets a PR boost. This increases the probability that customers visit her post office. Unfortunately, sometimes the robbers succeed. This decreases the probability that customers enter the post office. Adjust the parameters of the simulation and click PLAY to start the simulation. Then step through the simulation by pressing the SPACE key. At the end the statistics of the simulation will be summarised."
            
            # Wrap raw_text manually and blit lines
            x = 70
            y = 80
            chars_per_line = 130
            cut = False
            last_cut_idx = 0
            line_count = 0
            for i in range(1, len(raw_text), 1):
                if i % chars_per_line == 0:
                    cut = True
                if i == len(raw_text) - 1 or (raw_text[i] in [' ', '\n', '\t'] and cut):
                    text = self.font_IBM_2y.render(raw_text[last_cut_idx:i+1].strip(), False, self.BLACK)
                    text_rect = text.get_rect()
                    text_rect.x = x
                    text_rect.y = y + text_rect.h * line_count
                    self.rects[key].append((text, text_rect))

                    line_count += 1
                    last_cut_idx = i
                    cut = False


        # Blit rects
        for rect in self.rects[key]:
                self.screen.blit(rect[0], rect[1])

    def blit_parameter_names(self):
        key = "parameter_names"

        # Generate parameter name rects
        if key not in self.rects.keys():
            parameter_names = [
                "Opening time",
                "Closing time",
                "Probability a customer enters every minute",
                "Number of minutes it takes Franco to finish a customer's task",
                "Probability a robbery occurs every minute",
                "Probability a robbery succeeds",
                "Probability a customer is killed in a robbery",
                "Probability boost a customer enters every minute after an unsuccessful robbery",
                "Probability drop a customer enters every minute after a successful robbery",
                "Coefficient to determine how long a probability boost or drop continues after a robbery"
            ]

            x = 70
            y = 300
            parameter_count = 0
            self.rects[key] = []
            for param_name in parameter_names:
                text = self.font_IBM.render(param_name, False, self.BLACK)
                text_rect = text.get_rect()
                text_rect.x = x
                text_rect.y = y + (text_rect.h + 2) * parameter_count
                self.rects[key].append((text, text_rect))
                parameter_count += 1

        for param in self.rects[key]:
            self.screen.blit(param[0], param[1])

    def blit_parameter_inputs(self, mouse_x, mouse_y, left_clicked):

        # Initialise parameter input boxes
        if not self.input_boxes:
            for param in self.rects["parameter_names"]:
                rect = param[1]
                box = InputBox(rect.x + rect.w + 20, rect.y, 100, rect.h, self.font_IBM_2y, self.WHITE, self.BLACK)
                self.input_boxes.append(box)

        hovering = False
        for box in self.input_boxes:
            if box.hovering(mouse_x, mouse_y):
                hovering = True
                if left_clicked:
                    box.taking_input = True

        # No box taking input
        if not hovering and left_clicked:
            for box in self.input_boxes:
                box.taking_input = False

        # Determine cursor shape
        if hovering:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_IBEAM)
        else:
            if pygame.mouse.get_cursor() == pygame.SYSTEM_CURSOR_IBEAM:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        # Dislay input boxes
        for box in self.input_boxes:
            box.blit(self.screen)
    
    def run(self, postoffice: PostOffice):
        self.stage = 0

        while True:

            # Check if an input box is taking keyboard input
            active_box_idx = -1
            for i in range(len(self.input_boxes)):
                if self.input_boxes[i].taking_input:
                    active_box_idx = i
                    break

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

                # Update input text of box if there is an active one
                if active_box_idx != -1:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_BACKSPACE:
                            if self.input_boxes[active_box_idx].input_text != "":
                                self.input_boxes[active_box_idx].input_text = self.input_boxes[active_box_idx].input_text[:-1]
                        else:
                            char = event.unicode
                            if char.isnumeric() or char.isalpha() or char in [',', '.', ':']:
                                self.input_boxes[active_box_idx].input_text += event.unicode

            self.screen.fill("black")

            #
            # Franco's Post Office logic
            #
            
            delay_frame = 0

            # Keyboard input
            space_pressed = False
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                space_pressed = True

            # Mouse input
            mouse_x, mouse_y = pygame.mouse.get_pos()
            left_clicked = pygame.mouse.get_pressed()[0]

            # Main menu
            if self.stage == 0:
                if space_pressed:
                    self.set_bg(self.bg0_pressed)
                    self.stage = 1
                    self.rects.clear()
                    delay_frame = 300
                else:
                    self.set_bg(self.bg0)

            # Choose parameters before simulation 
            elif self.stage == 1:

                # TODO: Write function to determine cursor shape by having a centralized way of storing objects drawn
                # TODO: Write function "progress_stage()" which automatically handles all the changes made between each stage 
                if self.clicked_play_button(mouse_x, mouse_y, left_clicked):
                    self.rects.clear()
                    delay_frame = 300
                    self.stage = 2
                
                # Instructions
                self.blit_how_to()

                # Parameter selection
                self.blit_parameter_names()
                self.blit_parameter_inputs(mouse_x, mouse_y, left_clicked)

            # Simulation
            elif self.stage == 2:
                if space_pressed:
                    self.set_bg(self.bg2_pressed)
                    postoffice.simulate(self)
                else:
                    self.set_bg(self.bg2)
                self.blit_logs()

            # End of simulation statistics
            else:
                pass

            #
            # END Franco's Post Office logic
            #

            pygame.display.flip()
            self.clock.tick(60)
            if delay_frame:
                pygame.time.delay(delay_frame)



def main():
    gui = GUI(1200, 800)
    postoffice = PostOffice()
    gui.run(postoffice)

if __name__ == "__main__":
    main()
