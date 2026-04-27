import time
import L1_motor as m

# --- CONSTANTS ---
LIFT_SPEED = 0.8     # Adjust based on motor strength
LIFT_DURATION = 2.0  # Seconds to let the lift motor run
DRIVE_SPEED = 0.5    # Speed for the wheels
DRIVE_TIME = 2.0     # How long to drive forward to scoop the object

def lower_fork():
    print("[ACTION] Lowering fork...")
    m.lift(-LIFT_SPEED) 
    time.sleep(LIFT_DURATION)
    m.lift(0) # Stop lift

def lift_fork():
    print("[ACTION] Lifting fork...")
    m.lift(LIFT_SPEED)
    time.sleep(LIFT_DURATION)
    m.lift(0) # Stop lift

def drive(speed, duration):
    """Helper function to drive for a set amount of time and stop."""
    m.set_speeds(speed, speed)
    time.sleep(duration)
    m.stop()

def demo_sequence():
    print("🎬 Starting Pick-and-Move Demo in 3 seconds...")
    print("⚠️ Make sure the target object is directly in front of the robot!")
    time.sleep(3)

    # Step 1: Reset position
    print("\n--- Step 1: Preparing ---")
    lower_fork()
    time.sleep(1)

    # Step 2: Scoop
    print("\n--- Step 2: Scooping Object ---")
    print("Driving forward...")
    drive(DRIVE_SPEED, DRIVE_TIME) 
    time.sleep(0.5) # Brief pause for dramatic effect

    # Step 3: Lift
    print("\n--- Step 3: Lifting Object ---")
    lift_fork()
    time.sleep(1)

    # Step 4: Transport
    print("\n--- Step 4: Transporting ---")
    print("Reversing with the payload...")
    drive(-DRIVE_SPEED, DRIVE_TIME)
    time.sleep(1)

    # Step 5: Drop
    print("\n--- Step 5: Dropping Object ---")
    lower_fork()
    time.sleep(0.5)

    # Step 6: Clear the area
    print("\n--- Step 6: Backing Away ---")
    drive(-DRIVE_SPEED, 1.5)

    print("\n✅ Pick-and-Move Demo Complete.")

if __name__ == "__main__":
    demo_sequence()