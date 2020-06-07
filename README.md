# Dissertation: Automating Locomotion Animation in Maya using a Deep Neural Network

This repo contains the code for my Master's dissertation, along with the dissertation itself.

## Summary
For my thesis I developed a Python plugin for Maya, a 3D animation software. The user selects a character and a path and the plugin animates the character's locomotion along the path. The provided animation is adaptive to different terrains and can provide a number of different locomotion types, including walking, crouching and running. The plugin communicates with a cloud-hosted deep neural network to animate the character frame-by-frame. The neural network is implemented in C++ and was taken from a 2017 research paper, ['Phase-Functioned Neural Networks for Character Control'](http://theorangeduck.com/media/uploads/other_stuff/phasefunction.pdf) by Daniel Holden et al. The implementation of this was taken from [Sreya Francis](https://github.com/sreyafrancis/PFNN) on github, and adapted by me to run on Google Cloud Platform. The neural net is trained on motion capture data to provide realistic locomotion that can adapt to terrains to a reasonable degree of accuracy.

This was a cross-disciplinary project covering 3D animation, deep learning, computational geometry and cloud computing.

## Videos
Follow [this link](https://drive.google.com/drive/folders/1fxyfG2KJZksDpBAxe8l9u_PKlUjSoW0b) to find a number of videos showing the animations in action. There is a README in this folder further explaining the contents of each video. For a highlight reel, see `0_full_demo.mp4`.

## Further Reading
For a more in-depth look at the work I completed, please see `Dissertation.pdf` in the root directory of this repo. In particular, the Executive Summary gives a high-level look at the work undertaken in this project.
