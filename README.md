<p align="center">
    <br>
    <img src="https://github.com/antonioverdi/Text-Generation-GUI/blob/master/docs/imgs/happy-robot.png" width="200"/>
    <br>
<p>
<h1 align="center">
<p> Rovr </p>
</h1>

## Table of Contents

- [Getting Started](#getting-started)
- [Phase 1 - Basic Tracking](#phase-1)
- [Phase 2 - Search and (Not) Destroy](#phase-2)
- [Copyright and License](#copyright-and-license)

## Getting Started
- One thing to note before getting started is the fact that I will often be referring to the object as though it’s position is not static. Essentially what I mean is that i will be talking as though the object we want to track will be moving through space, because in my case the object I want to track is my cat (Insert cat photo here). Obviously the rover will have the ability to detect and move towards static objects as well, but in my eyes it’s more fun to have the rover track down something that is moving.

Now on to the actual setup: 
- For the sake of simplicity, we can setup the Pi using the steps in the following GitHub repo
- Once that has been done, we want to make sure that all the files we will need, including the labels.csv file and model for inference, are contained in a folder on the Pi
- Again for the sake of simplicity, when it comes to the actual movement of the car, we will be relying on the code base provided by sunfounder

## Phase 1 - Basic Tracking
- In phase 1, the goal will be to set up the car such that it can detect the desired object and move towards it using only the input from the webcam
- To do this, we will run inference on the frames we receive as input from the webcam using OpenCV and calculate the location of the object relative to the car using the location of the bounding boxes on the screen
- Once the location of the object has been determined, we can instruct the rover to move in the correct detection to follow the object (assuming it is moving)

### Phase 1.5
- In phase 1.5, the overall goal is the same with the exception that we will add an ultrasonic sensor to the car to be able to better navigate the environment and avoid obstacles

## Phase 2 - Search and (Don't) Destroy
- In phase 2, we take everything implemented in phase 1 and apply it to a more slightly more difficult task. That is, we want to specify an object and instruct the rover to navigate the entire space until it has found the object
    - Note that we also want to eventually have it so that the rover can determine if the object is not present in the space, but that would mean it would have to verify it has inspected the entire space
- In order to do this, we will have the rover move around the space until the desired object is found within the frame. Once the object has been located, we can simply run the same code we wrote in phase 1 and have the rover actively follow the object.
    - We could also have the rover perform some operation or play a sound once the object has been located
