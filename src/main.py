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


class GUI:
    BLACK = (0,0,0)

    def __init__(self, width, height):
        pygame.init()
        pygame.display.set_caption("Franco's Post Office")

        self.width = width
        self.height = height

        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font("lib/Hack-Regular.ttf", 16)

        self.bg = pygame.image.load("lib/bg.png")
        self.screen.blit(self.bg, (0, 0))

        self.logs = []

    def log(self, a: str):
        self.logs.append(a)
        if len(self.logs) > 10:
            self.logs.pop(0)

    def blit_logs(self):
        x = self.width // 8
        for i, log in enumerate(self.logs):
            text = self.font.render(log, True, self.BLACK)
            text_rect = text.get_rect()
            text_rect.x = x
            text_rect.y = self.height // (4/3) + text_rect.h * i
            self.screen.blit(text, text_rect)

    def run(self, postoffice: PostOffice):
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            self.screen.fill("black")
            self.screen.blit(self.bg, (0,0))

            # Simulation
            
            key_pressed = False
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                key_pressed = True
                postoffice.simulate(self)

            self.blit_logs()

            # END Simulation

            pygame.display.flip()
            self.clock.tick(60)

            # Delay 500 milliseconds if key pressed to avoid spam
            if key_pressed:
                pygame.time.delay(500)

        pygame.quit()
        quit()



def main():
    gui = GUI(1200, 800)
    postoffice = PostOffice()
    gui.run(postoffice)

if __name__ == "__main__":
    main()
