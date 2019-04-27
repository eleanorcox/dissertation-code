# Maya Binary Files Explained

This document is an explanation of the ever-growing number of Maya files I have and what each shows.

| File Name | File Description | Animation | Character Rest Position | Path Type | Terrain Type |
| --------- | ---------------- | :-------: | :---------------------: | :-------: | :----------: |
| skeleton.mb  | Initial skeleton based off BVH file from PFNN training data. | N/A  | T-Pose  | N/A  | N/A  |
| skeleton_demo.mb  | For use with maya_demo.py and loco_demo.py. Reads in test outputs from the model and animates the character moving according to these. For demonstrating joint movement. This was used to show my progress during the project poster fair.| N/A  | T-Pose  | N/A  | Flat  |
| demo_run_repeated_segments | An animation created from PFNN test outputs. These outputs feature multiple repeated segments of animation, with each segment taking 20-100 frames and being repeated 10 times. The character moves on the spot. | Yes - 8000 frames  | Posed  | N/A  | Flat  |
| demo_run_stitched_segments  | An animation created by stitching together appropriate segments from the PFNN test output (as seen in demo_run_repeated_segments). As such this looks less choppy. Character still moves on the spot as no root velocity is taken into consideration. |  Yes - 350 frames | Posed  | N/A | Flat |
|   |   |   |   |   |   |
| testing_curve_flat | For testing. | N/A | Posed | Curve | Flat |
| testing_curve_rough | For testing terrain heights (rough terrain)  |  N/A | Posed  | Curve  | Rough   |
| testing_straight_flat | For testing. Flat terrain, straight path that is 800 units long with equidistant edit points. | N/A | Posed | Straight | Flat |
|   |   |   |   |   |   |
| walk_broken_noRootXform.mb | Broken walk animation, uses local joint positions. Doesn't use rootxform so character does not walk along path appropriately, instead sliding and walking almost on-the-spot. | Yes - 800 frames  | Posed  | Curve  | N/A  |
|  walk_broken_wrongPath | Broken walk animation.  Attempted to use root x/z velocities to move character along the path. This didn't work as intended so character walked completely off the path. Joints move fine but root transform is wrong. No heights as at this point was still trying to get path working. | Yes - 800 frames  | Posed  |  Curve | N/A  |
| walk_correctPath | Character walking along path. No terrain so no height information - was created purely from joint positions along path. | Yes - 800 frames  | Posed  | Curve  |  N/A |
|   |   |   |   |   |   |
|  heights_naive_sampling | Demonstrates the issues with naive height sampling - the character often walks above/below the terrain inappropriately and the heights are choppily sampled.  | Yes - 345 frames  | Posed  | Curve  |  Rough |
| heights_interpolated_sampling  |  Demonstrates the improvement in animation when using interpolation while sampling heights | Yes - 800 frames  | Posed  | Curve  | Rough  |
|   |   |   |   |   |   |
| path_naive_sampling_X | These demonstrate the broken method of path sampling. Here the path is sampled equidistantly at 800 points, meaning the animation only looks correct if you happen to have an appropriate number of frames. This means the animation looks wrong for most types of locomotion, with a lot of sliding or too small steps, and will alter greatly depending on the path length/locomotion. X = {bump, crouch, jump, run, stand, walk} | Yes - 800 frames each  | Posed  | Curve  | Flat  |
| path_naive_sampling_mixed  | Demonstration of the issues with naive path sampling. For this, the path was sampled at equidistant points for 800 frames, and the character directed to walk, jog then walk for each third of the animation (i.e. gait of 1, 2, 1). The walking animation looks OK as this sampling rate is good for walking, but the jogging section looks strange as the character does not move horizontally enough for the jogging action, instead looking squashed. There is no blending between the gaits so the character changes between these relatively abruptly.  | Yes - 800 frames  | Posed  | Straight  | Flat  |
| path_stand_10000_translationTest | When directed to stand, the character exhibits some secondary motion such as shuffling from foot to foot. Based on this I decided to test whether it was appropriate to have the character move forward slightly when standing. The path was sampled 10,000 times and it is clear that the chracter moving provides a strange gliding motion, even with the seconday motions considered, and so I concluded that when standing the character's root transform should not move. | Yes - 10000 frames  | Posed  | Straight  | Flat  |
| path_walk_X | For trying to establish a good path sampling rate for walking. In each file, the path is sampled at X equidistant points. These animations are then inspected manually to choose which has the best sampling rate. X = {650, 750, 775, 780, 800} frames. |  Yes - X frames | Posed  | Straight  | Flat  |
| path_run_X | For trying to establish a good path sampling rate for jogging. In each file, the path is sampled at X equidistant points. These animations are then inspected manually to choose which has the best sampling rate. X = {200, 250, 300, 500} frames. | Yes - X frames  |  Posed | Straight  | Flat  |
| path_improved_sampling   | Demonstration of improved path sampling. In this animation the character walks for the first half then jogs for the second (i.e. gait = 1,2). Appropriate sampling rates were calculated for standing, walking and jogging and then these are used to create the animation. The user defines what type of locomotion they want at soecific points along the path and the program calculates the appropriate number of frames for the total animation - thus the user can no longer choose the number of frames they want, but the animation quality increases significantly and they are not having to trial and error with different numbers of frames. There is no blending between the gaits so the change is still somewhat abrupt. | Yes - 515 frames  | Posed  | Straight  | Flat  |
|   |   |   |   |   |   |

**NOT DONE:** gait_X_X_X, path_crouch_X, pfnn_X_walk_780
