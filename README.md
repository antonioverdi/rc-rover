
<h1 align="center">
<p> RC-ROVER </p>
<p> An Object-Tracking RC Car built with the Raspberry Pi 4</p>
</h1>

<p align="center">
    <br>
    <img src=images/rover.jpg width="750"/>
    <br>
<p>


## Table of Contents

- [Getting Started](#getting-started)
- [Phase 1 - Basic Tracking](#phase-1---basic-tracking)
- [Phase 2 - Object Search](#phase-2---object-search)
- [Resources](#resources)
- [Copyright and License](#copyright-and-license)

## Getting Started
At this point in time, the code is setup to run on the Sunfound PiCar-V using the control libraries they have written for the hardware in the car. If the code is to be run on different hardware, the cat_tracker.py file will need to be adjusted when it comes to the actual movement of the car. If 

### Running the Code
Assuming you have a Sunfounder PiCar-V setup as directed in their manual, all you have to do is clone the github repo and run the cat_tracker.py file.

## Phase 1 - Basic Tracking
- In phase 1, the goal will be to set up the car such that it can detect the desired object and move towards it using only the input from the webcam
- To do this, we will run inference on the frames we receive as input from the webcam using OpenCV and calculate the location of the object relative to the car using the location of the bounding boxes on the screen
- Once the location of the object has been determined, we can instruct the rover to move in the correct detection to move towards the object until it reaches the distance threshold, at which point it will stop.

### Phase 2
Th next phase is still a work in progress. As of right now, the car just sits in a static location and scans in front of it until it detects a cat. Moving forward, the goal will be to implement a SLAM algorithm so that the car can patrol the house while scanning for objects

## Resources
Here I will be listing the resources used when building the project, whether they be online tutorials, articles, or codebases from github.

**Sunfounder PiCar-V Git Repo** [https://github.com/sunfounder/SunFounder_PiCar-V](https://github.com/sunfounder/SunFounder_PiCar-V)

- Used for general car utilities

- Used for implementing tensorflow detection models



