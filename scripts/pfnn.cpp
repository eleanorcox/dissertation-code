#include <eigen3/Eigen/Dense>

#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <glm/gtc/type_ptr.hpp>
#include <glm/gtx/quaternion.hpp>
#include <glm/gtx/transform.hpp>

#include <stdlib.h>
#include <iostream>
#include <stdio.h>
#include <sstream>
#include <fstream>
#include <string>
#include <vector>

#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <nlohmann/json.hpp>

#include <stdarg.h>
#include <time.h>

using namespace Eigen;
using json = nlohmann::json;

/* Helper Functions */

// Error function for networking
void error(const char *msg) {
	perror(msg);
	exit(1);
}

static glm::quat quat_exp(glm::vec3 l) {
  float w = glm::length(l);
  glm::quat q = w < 0.01 ? glm::quat(1,0,0,0) : glm::quat(
    cosf(w),
    l.x * (sinf(w) / w),
    l.y * (sinf(w) / w),
    l.z * (sinf(w) / w));
  return q / sqrtf(q.w*q.w + q.x*q.x + q.y*q.y + q.z*q.z);
}

/* Phase-Functioned Neural Network */

struct PFNN {

  enum { XDIM = 342, YDIM = 311, HDIM = 512 };
  enum { MODE_CONSTANT, MODE_LINEAR, MODE_CUBIC };

  int mode;

  ArrayXf Xmean, Xstd;
  ArrayXf Ymean, Ystd;

  std::vector<ArrayXXf> W0, W1, W2;
  std::vector<ArrayXf>  b0, b1, b2;

  ArrayXf  Xp, Yp;
  ArrayXf  H0,  H1;
  ArrayXXf W0p, W1p, W2p;
  ArrayXf  b0p, b1p, b2p;

  PFNN(int pfnnmode)
    : mode(pfnnmode) {

    Xp = ArrayXf((int)XDIM);
    Yp = ArrayXf((int)YDIM);

    H0 = ArrayXf((int)HDIM);
    H1 = ArrayXf((int)HDIM);

    W0p = ArrayXXf((int)HDIM, (int)XDIM);
    W1p = ArrayXXf((int)HDIM, (int)HDIM);
    W2p = ArrayXXf((int)YDIM, (int)HDIM);

    b0p = ArrayXf((int)HDIM);
    b1p = ArrayXf((int)HDIM);
    b2p = ArrayXf((int)YDIM);
  }

  static void load_weights(ArrayXXf &A, int rows, int cols, const char* fmt, ...) {
    va_list valist;
    va_start(valist, fmt);
    char filename[512];
    vsprintf(filename, fmt, valist);
    va_end(valist);

    FILE *f = fopen(filename, "rb");
    if (f == NULL) { fprintf(stderr, "Couldn't load file %s\n", filename); exit(1); }

    A = ArrayXXf(rows, cols);
    for (int x = 0; x < rows; x++)
    for (int y = 0; y < cols; y++) {
      float item = 0.0;
      fread(&item, sizeof(float), 1, f);
      A(x, y) = item;
    }
    fclose(f);
  }

  static void load_weights(ArrayXf &V, int items, const char* fmt, ...) {
    va_list valist;
    va_start(valist, fmt);
    char filename[512];
    vsprintf(filename, fmt, valist);
    va_end(valist);

    FILE *f = fopen(filename, "rb");
    if (f == NULL) { fprintf(stderr, "Couldn't load file %s\n", filename); exit(1); }

    V = ArrayXf(items);
    for (int i = 0; i < items; i++) {
      float item = 0.0;
      fread(&item, sizeof(float), 1, f);
      V(i) = item;
    }
    fclose(f);
  }

  void load() {

    load_weights(Xmean, XDIM, "./network/pfnn/Xmean.bin");
    load_weights(Xstd,  XDIM, "./network/pfnn/Xstd.bin");
    load_weights(Ymean, YDIM, "./network/pfnn/Ymean.bin");
    load_weights(Ystd,  YDIM, "./network/pfnn/Ystd.bin");

    switch (mode) {

      case MODE_CONSTANT:

        W0.resize(50); W1.resize(50); W2.resize(50);
        b0.resize(50); b1.resize(50); b2.resize(50);

        for (int i = 0; i < 50; i++) {
          load_weights(W0[i], HDIM, XDIM, "./network/pfnn/W0_%03i.bin", i);
          load_weights(W1[i], HDIM, HDIM, "./network/pfnn/W1_%03i.bin", i);
          load_weights(W2[i], YDIM, HDIM, "./network/pfnn/W2_%03i.bin", i);
          load_weights(b0[i], HDIM, "./network/pfnn/b0_%03i.bin", i);
          load_weights(b1[i], HDIM, "./network/pfnn/b1_%03i.bin", i);
          load_weights(b2[i], YDIM, "./network/pfnn/b2_%03i.bin", i);
        }

      break;

      case MODE_LINEAR:

        W0.resize(10); W1.resize(10); W2.resize(10);
        b0.resize(10); b1.resize(10); b2.resize(10);

        for (int i = 0; i < 10; i++) {
          load_weights(W0[i], HDIM, XDIM, "./network/pfnn/W0_%03i.bin", i * 5);
          load_weights(W1[i], HDIM, HDIM, "./network/pfnn/W1_%03i.bin", i * 5);
          load_weights(W2[i], YDIM, HDIM, "./network/pfnn/W2_%03i.bin", i * 5);
          load_weights(b0[i], HDIM, "./network/pfnn/b0_%03i.bin", i * 5);
          load_weights(b1[i], HDIM, "./network/pfnn/b1_%03i.bin", i * 5);
          load_weights(b2[i], YDIM, "./network/pfnn/b2_%03i.bin", i * 5);
        }

      break;

      case MODE_CUBIC:

        W0.resize(4); W1.resize(4); W2.resize(4);
        b0.resize(4); b1.resize(4); b2.resize(4);

        for (int i = 0; i < 4; i++) {
          load_weights(W0[i], HDIM, XDIM, "./network/pfnn/W0_%03i.bin", (int)(i * 12.5));
          load_weights(W1[i], HDIM, HDIM, "./network/pfnn/W1_%03i.bin", (int)(i * 12.5));
          load_weights(W2[i], YDIM, HDIM, "./network/pfnn/W2_%03i.bin", (int)(i * 12.5));
          load_weights(b0[i], HDIM, "./network/pfnn/b0_%03i.bin", (int)(i * 12.5));
          load_weights(b1[i], HDIM, "./network/pfnn/b1_%03i.bin", (int)(i * 12.5));
          load_weights(b2[i], YDIM, "./network/pfnn/b2_%03i.bin", (int)(i * 12.5));
        }

      break;
    }

  }

  static void ELU(ArrayXf &x) { x = x.max(0) + x.min(0).exp() - 1; }

  static void linear(ArrayXf  &o, const ArrayXf  &y0, const ArrayXf  &y1, float mu) { o = (1.0f-mu) * y0 + (mu) * y1; }
  static void linear(ArrayXXf &o, const ArrayXXf &y0, const ArrayXXf &y1, float mu) { o = (1.0f-mu) * y0 + (mu) * y1; }

  static void cubic(ArrayXf  &o, const ArrayXf &y0, const ArrayXf &y1, const ArrayXf &y2, const ArrayXf &y3, float mu) {
    o = (
      (-0.5*y0+1.5*y1-1.5*y2+0.5*y3)*mu*mu*mu +
      (y0-2.5*y1+2.0*y2-0.5*y3)*mu*mu +
      (-0.5*y0+0.5*y2)*mu +
      (y1));
  }

  static void cubic(ArrayXXf &o, const ArrayXXf &y0, const ArrayXXf &y1, const ArrayXXf &y2, const ArrayXXf &y3, float mu) {
    o = (
      (-0.5*y0+1.5*y1-1.5*y2+0.5*y3)*mu*mu*mu +
      (y0-2.5*y1+2.0*y2-0.5*y3)*mu*mu +
      (-0.5*y0+0.5*y2)*mu +
      (y1));
  }

  void predict(float P) {

    float pamount;
    int pindex_0, pindex_1, pindex_2, pindex_3;

    Xp = (Xp - Xmean) / Xstd;

    switch (mode) {

      case MODE_CONSTANT:
        pindex_1 = (int)((P / (2*M_PI)) * 50);
        H0 = (W0[pindex_1].matrix() * Xp.matrix()).array() + b0[pindex_1]; ELU(H0);
        H1 = (W1[pindex_1].matrix() * H0.matrix()).array() + b1[pindex_1]; ELU(H1);
        Yp = (W2[pindex_1].matrix() * H1.matrix()).array() + b2[pindex_1];
      break;

      case MODE_LINEAR:
        pamount = fmod((P / (2*M_PI)) * 10, 1.0);
        pindex_1 = (int)((P / (2*M_PI)) * 10);
        pindex_2 = ((pindex_1+1) % 10);
        linear(W0p, W0[pindex_1], W0[pindex_2], pamount);
        linear(W1p, W1[pindex_1], W1[pindex_2], pamount);
        linear(W2p, W2[pindex_1], W2[pindex_2], pamount);
        linear(b0p, b0[pindex_1], b0[pindex_2], pamount);
        linear(b1p, b1[pindex_1], b1[pindex_2], pamount);
        linear(b2p, b2[pindex_1], b2[pindex_2], pamount);
        H0 = (W0p.matrix() * Xp.matrix()).array() + b0p; ELU(H0);
        H1 = (W1p.matrix() * H0.matrix()).array() + b1p; ELU(H1);
        Yp = (W2p.matrix() * H1.matrix()).array() + b2p;
      break;

      case MODE_CUBIC:
        pamount = fmod((P / (2*M_PI)) * 4, 1.0);
        pindex_1 = (int)((P / (2*M_PI)) * 4);
        pindex_0 = ((pindex_1+3) % 4);
        pindex_2 = ((pindex_1+1) % 4);
        pindex_3 = ((pindex_1+2) % 4);
        cubic(W0p, W0[pindex_0], W0[pindex_1], W0[pindex_2], W0[pindex_3], pamount);
        cubic(W1p, W1[pindex_0], W1[pindex_1], W1[pindex_2], W1[pindex_3], pamount);
        cubic(W2p, W2[pindex_0], W2[pindex_1], W2[pindex_2], W2[pindex_3], pamount);
        cubic(b0p, b0[pindex_0], b0[pindex_1], b0[pindex_2], b0[pindex_3], pamount);
        cubic(b1p, b1[pindex_0], b1[pindex_1], b1[pindex_2], b1[pindex_3], pamount);
        cubic(b2p, b2[pindex_0], b2[pindex_1], b2[pindex_2], b2[pindex_3], pamount);
        H0 = (W0p.matrix() * Xp.matrix()).array() + b0p; ELU(H0);
        H1 = (W1p.matrix() * H0.matrix()).array() + b1p; ELU(H1);
        Yp = (W2p.matrix() * H1.matrix()).array() + b2p;
      break;

      default:
      break;
    }

    Yp = (Yp * Ystd) + Ymean;
  }

};

static PFNN* pfnn = NULL;

/* Character */

struct Character {

	enum { JOINT_NUM = 31 };

	float phase;

	glm::vec3 joint_positions[JOINT_NUM];	// World space
	glm::vec3 joint_velocities[JOINT_NUM];	// World space
	glm::mat3 joint_rotations[JOINT_NUM];

	Character()
	: phase(0) {}

};

static Character* character = NULL;

/* Trajectory */

struct Trajectory {

	enum { LENGTH = 120 };

	glm::vec3 positions[LENGTH];	// World space
	glm::vec3 directions[LENGTH];	// World space
	glm::mat3 rotations[LENGTH];	// World space
	float heights[LENGTH][3];		// World space

	float gait_stand[LENGTH];
	float gait_walk[LENGTH];
	float gait_jog[LENGTH];
	float gait_crouch[LENGTH];
	float gait_jump[LENGTH];
	float gait_bump[LENGTH];

};

static Trajectory* trajectory = NULL;

/* Reset */

static void reset() {

 	ArrayXf Yp = pfnn->Ymean;

	glm::vec3 root_position = glm::vec3(0.0, 0.0, 0.0);
 	glm::mat3 root_rotation = glm::mat3();

	for (int i = 0; i < Trajectory::LENGTH; i++) {
		trajectory->positions[i] = root_position;
		trajectory->rotations[i] = root_rotation;
		trajectory->directions[i] = glm::vec3(0.0, 0.0, 1.0);
		trajectory->heights[i][0] = root_position.y;
		trajectory->heights[i][1] = root_position.y;
		trajectory->heights[i][2] = root_position.y;
		trajectory->gait_stand[i] = 0.0;
		trajectory->gait_walk[i] = 0.0;
		trajectory->gait_jog[i] = 0.0;
		trajectory->gait_crouch[i] = 0.0;
		trajectory->gait_jump[i] = 0.0;
		trajectory->gait_bump[i] = 0.0;
	}

	for (int i = 0; i < Character::JOINT_NUM; i++) {
		int opos = 8+(((Trajectory::LENGTH/2)/10)*4)+(Character::JOINT_NUM*3*0);
		int ovel = 8+(((Trajectory::LENGTH/2)/10)*4)+(Character::JOINT_NUM*3*1);
		int orot = 8+(((Trajectory::LENGTH/2)/10)*4)+(Character::JOINT_NUM*3*2);

		glm::vec3 pos = (root_rotation * glm::vec3(Yp(opos+i*3+0), Yp(opos+i*3+1), Yp(opos+i*3+2))) + root_position;
		glm::vec3 vel = (root_rotation * glm::vec3(Yp(ovel+i*3+0), Yp(ovel+i*3+1), Yp(ovel+i*3+2)));
		glm::mat3 rot = (root_rotation * glm::toMat3(quat_exp(glm::vec3(Yp(orot+i*3+0), Yp(orot+i*3+1), Yp(orot+i*3+2)))));

		character->joint_positions[i]  = pos;
		character->joint_velocities[i] = vel;
		character->joint_rotations[i]  = rot;
	}

	character->phase = 0.0;

}

/* Initialise character and trajectory from input from loco */

void initialiseCharacter(json json_msg) {

	/* Initialise Joint Positions */
	for(int i = 0; i < Character::JOINT_NUM; i++){
		float x = json_msg["JointPos"][i*3 + 0];
		float y = json_msg["JointPos"][i*3 + 1];
		float z = json_msg["JointPos"][i*3 + 2];
		character->joint_positions[i] = glm::vec3(x, y, z);
	}

	/* Initialise Joint Velocities */
	for(int i = 0; i < Character::JOINT_NUM; i++){
		float x = json_msg["JointVel"][i*3 + 0];
		float y = json_msg["JointVel"][i*3 + 1];
		float z = json_msg["JointVel"][i*3 + 2];
		character->joint_velocities[i] = glm::vec3(x, y, z);
	}
}

void initialiseTrajectory(json json_msg) {

	// TODO: assumes character starts exactly on trajectory. what if this is not the case?
	// Trajectory has to originate from character root position. edit in Maya to force this to be the case.

	// TODO: assumes more than 60 frames.

	/* Initialise Trajectory Positions */
	for(int i = 0; i < Trajectory::LENGTH/2; i++){
		float past_posx = json_msg["PathPos"][0][0];
		float past_posy = json_msg["PathHeight"][0][1];
		float past_posz = json_msg["PathPos"][0][1];
		trajectory->positions[i] = glm::vec3(past_posx, past_posy, past_posz);

		float posx = json_msg["PathPos"][i][0];
		float posy = json_msg["PathHeight"][i][1];
		float posz = json_msg["PathPos"][i][1];
		trajectory->positions[Trajectory::LENGTH/2 + i] = glm::vec3(posx, posy, posz);
	}

	/* Initialise Trajectory Directions */
	for(int i = 0; i < Trajectory::LENGTH/2; i++){
		float past_dirx = json_msg["PathDir"][0][0];
		float past_diry = 0.0;
		float past_dirz = json_msg["PathDir"][0][1];
		trajectory->directions[i] = glm::vec3(past_dirx, past_diry, past_dirz);

		float dirx = json_msg["PathDir"][i][0];
		float diry = 0.0;
		float dirz = json_msg["PathDir"][i][1];
		trajectory->directions[Trajectory::LENGTH/2 + i] = glm::vec3(dirx, diry, dirz);
	}

	/* Initialise Trajectory Rotations */
	for(int i = 0; i < Trajectory::LENGTH; i++){
		trajectory->rotations[i] = glm::mat3(glm::rotate(atan2f(
			trajectory->directions[i].x,
			trajectory->directions[i].z), glm::vec3(0,1,0)));
	}

	/* Initialise Trajectory Heights */
	for(int i = 0; i < Trajectory::LENGTH/2; i++){
		float past_height_r = json_msg["PathHeight"][0][0];
		float past_height_c = json_msg["PathHeight"][0][1];
		float past_height_l = json_msg["PathHeight"][0][2];
		trajectory->heights[i][0] = past_height_r;
		trajectory->heights[i][1] = past_height_c;
		trajectory->heights[i][2] = past_height_l;

		float height_r = json_msg["PathHeight"][i][0];
		float height_c = json_msg["PathHeight"][i][1];
		float height_l = json_msg["PathHeight"][i][2];
		trajectory->heights[Trajectory::LENGTH/2 + i][0] = height_r;
		trajectory->heights[Trajectory::LENGTH/2 + i][1] = height_c;
		trajectory->heights[Trajectory::LENGTH/2 + i][2] = height_l;
	}

	/* Initialise Gait */
	for(int i = 0; i < Trajectory::LENGTH/2; i++){
		float past_gait_index = json_msg["Gait"][0];
		if(past_gait_index == 0) {
			trajectory->gait_stand[i]  = 1.0;
			// trajectory->gait_walk[i] 	 = 0.0;
			// trajectory->gait_jog[i] 	 = 0.0;
			// trajectory->gait_crouch[i] = 0.0;
			// trajectory->gait_jump[i] 	 = 0.0;
			// trajectory->gait_bump[i] 	 = 0.0;
		}
		if(past_gait_index == 1) {
			// trajectory->gait_stand[i]  = 0.0;
			trajectory->gait_walk[i] 	 = 1.0;
			// trajectory->gait_jog[i] 	 = 0.0;
			// trajectory->gait_crouch[i] = 0.0;
			// trajectory->gait_jump[i] 	 = 0.0;
			// trajectory->gait_bump[i] 	 = 0.0;
		}
		if(past_gait_index == 2) {
			// trajectory->gait_stand[i]  = 0.0;
			// trajectory->gait_walk[i] 	 = 0.0;
			trajectory->gait_jog[i] 	 = 1.0;
			// trajectory->gait_crouch[i] = 0.0;
			// trajectory->gait_jump[i] 	 = 0.0;
			// trajectory->gait_bump[i] 	 = 0.0;
		}
		if(past_gait_index == 3) {
			// trajectory->gait_stand[i]  = 0.0;
			// trajectory->gait_walk[i] 	 = 0.0;
			// trajectory->gait_jog[i] 	 = 0.0;
			trajectory->gait_crouch[i] = 1.0;
			// trajectory->gait_jump[i] 	 = 0.0;
			// trajectory->gait_bump[i] 	 = 0.0;
		}
		if(past_gait_index == 4) {
			// trajectory->gait_stand[i]  = 0.0;
			// trajectory->gait_walk[i] 	 = 0.0;
			// trajectory->gait_jog[i] 	 = 0.0;
			// trajectory->gait_crouch[i] = 0.0;
			trajectory->gait_jump[i] 	 = 1.0;
			// trajectory->gait_bump[i] 	 = 0.0;
		}
		if(past_gait_index == 5) {
			// trajectory->gait_stand[i]  = 0.0;
			// trajectory->gait_walk[i] 	 = 0.0;
			// trajectory->gait_jog[i] 	 = 0.0;
			// trajectory->gait_crouch[i] = 0.0;
			// trajectory->gait_jump[i] 	 = 0.0;
			trajectory->gait_bump[i] 	 = 1.0;
		}

		float gait_index = json_msg["Gait"][i];
		if(gait_index == 0) {
			trajectory->gait_stand[Trajectory::LENGTH/2 + i]  = 1.0;
			// trajectory->gait_walk[Trajectory::LENGTH/2 + i] 	= 0.0;
			// trajectory->gait_jog[Trajectory::LENGTH/2 + i] 	  = 0.0;
			// trajectory->gait_crouch[Trajectory::LENGTH/2 + i] = 0.0;
			// trajectory->gait_jump[Trajectory::LENGTH/2 + i] 	= 0.0;
			// trajectory->gait_bump[Trajectory::LENGTH/2 + i] 	= 0.0;
		}
		if(gait_index == 1) {
			// trajectory->gait_stand[Trajectory::LENGTH/2 + i]  = 0.0;
			trajectory->gait_walk[Trajectory::LENGTH/2 + i] 	= 1.0;
			// trajectory->gait_jog[Trajectory::LENGTH/2 + i] 	  = 0.0;
			// trajectory->gait_crouch[Trajectory::LENGTH/2 + i] = 0.0;
			// trajectory->gait_jump[Trajectory::LENGTH/2 + i] 	= 0.0;
			// trajectory->gait_bump[Trajectory::LENGTH/2 + i] 	= 0.0;
		}
		if(gait_index == 2) {
			// trajectory->gait_stand[Trajectory::LENGTH/2 + i]  = 0.0;
			// trajectory->gait_walk[Trajectory::LENGTH/2 + i] 	= 0.0;
			trajectory->gait_jog[Trajectory::LENGTH/2 + i] 	  = 1.0;
			// trajectory->gait_crouch[Trajectory::LENGTH/2 + i] = 0.0;
			// trajectory->gait_jump[Trajectory::LENGTH/2 + i] 	= 0.0;
			// trajectory->gait_bump[Trajectory::LENGTH/2 + i] 	= 0.0;
		}
		if(gait_index == 3) {
			// trajectory->gait_stand[Trajectory::LENGTH/2 + i]  = 0.0;
			// trajectory->gait_walk[Trajectory::LENGTH/2 + i] 	= 0.0;
			// trajectory->gait_jog[Trajectory::LENGTH/2 + i] 	  = 0.0;
			trajectory->gait_crouch[Trajectory::LENGTH/2 + i] = 1.0;
			// trajectory->gait_jump[Trajectory::LENGTH/2 + i] 	= 0.0;
			// trajectory->gait_bump[Trajectory::LENGTH/2 + i] 	= 0.0;
		}
		if(gait_index == 4) {
			// trajectory->gait_stand[Trajectory::LENGTH/2 + i]  = 0.0;
			// trajectory->gait_walk[Trajectory::LENGTH/2 + i] 	= 0.0;
			// trajectory->gait_jog[Trajectory::LENGTH/2 + i] 	  = 0.0;
			// trajectory->gait_crouch[Trajectory::LENGTH/2 + i] = 0.0;
			trajectory->gait_jump[Trajectory::LENGTH/2 + i] 	= 1.0;
			// trajectory->gait_bump[Trajectory::LENGTH/2 + i] 	= 0.0;
		}
		if(gait_index == 5) {
			// trajectory->gait_stand[Trajectory::LENGTH/2 + i]  = 0.0;
			// trajectory->gait_walk[Trajectory::LENGTH/2 + i] 	= 0.0;
			// trajectory->gait_jog[Trajectory::LENGTH/2 + i] 	  = 0.0;
			// trajectory->gait_crouch[Trajectory::LENGTH/2 + i] = 0.0;
			// trajectory->gait_jump[Trajectory::LENGTH/2 + i] 	= 0.0;
			trajectory->gait_bump[Trajectory::LENGTH/2 + i] 	= 1.0;
		}
	}

}

/* Input the values for Xp in the PFNN */

void inputXp() {

	glm::vec3 root_position = glm::vec3(
	    trajectory->positions[Trajectory::LENGTH/2].x,
	    trajectory->heights[Trajectory::LENGTH/2][1],
	    trajectory->positions[Trajectory::LENGTH/2].z);

  	glm::mat3 root_rotation = trajectory->rotations[Trajectory::LENGTH/2];

	/* Input Trajectory Positions / Directions */
	for (int i = 0; i < Trajectory::LENGTH; i+=10) {
	    int w = (Trajectory::LENGTH)/10;
	    glm::vec3 pos = glm::inverse(root_rotation) * (trajectory->positions[i] - root_position);
	    glm::vec3 dir = glm::inverse(root_rotation) * trajectory->directions[i];
	    pfnn->Xp((w*0)+i/10) = pos.x; pfnn->Xp((w*1)+i/10) = pos.z;
	    pfnn->Xp((w*2)+i/10) = dir.x; pfnn->Xp((w*3)+i/10) = dir.z;
	}

	/* Input Gait */
	for (int i = 0; i < Trajectory::LENGTH; i+=10) {
		int w = (Trajectory::LENGTH)/10;
		pfnn->Xp((w*4)+i/10) = trajectory->gait_stand[i];
		pfnn->Xp((w*5)+i/10) = trajectory->gait_walk[i];
		pfnn->Xp((w*6)+i/10) = trajectory->gait_jog[i];
		pfnn->Xp((w*7)+i/10) = trajectory->gait_crouch[i];
		pfnn->Xp((w*8)+i/10) = trajectory->gait_jump[i];
		pfnn->Xp((w*9)+i/10) = 0.0; // Unused.
	}

	/* Input Joint Previous Positions / Velocities */
	glm::vec3 prev_root_position = glm::vec3(
		trajectory->positions[Trajectory::LENGTH/2-1].x,
		trajectory->heights[Trajectory::LENGTH/2-1][1],
		trajectory->positions[Trajectory::LENGTH/2-1].z);

	glm::mat3 prev_root_rotation = trajectory->rotations[Trajectory::LENGTH/2-1];

	for (int i = 0; i < Character::JOINT_NUM; i++) {
		int o = (((Trajectory::LENGTH)/10)*10);
		glm::vec3 pos = glm::inverse(prev_root_rotation) * (character->joint_positions[i] - prev_root_position);
		glm::vec3 prv = glm::inverse(prev_root_rotation) *  character->joint_velocities[i];
		pfnn->Xp(o+(Character::JOINT_NUM*3*0)+i*3+0) = pos.x;
		pfnn->Xp(o+(Character::JOINT_NUM*3*0)+i*3+1) = pos.y;
		pfnn->Xp(o+(Character::JOINT_NUM*3*0)+i*3+2) = pos.z;
		pfnn->Xp(o+(Character::JOINT_NUM*3*1)+i*3+0) = prv.x;
		pfnn->Xp(o+(Character::JOINT_NUM*3*1)+i*3+1) = prv.y;
		pfnn->Xp(o+(Character::JOINT_NUM*3*1)+i*3+2) = prv.z;
	}

	/* Input Trajectory Heights */
	for (int i = 0; i < Trajectory::LENGTH; i += 10) {
		int o = (((Trajectory::LENGTH)/10)*10)+Character::JOINT_NUM*3*2;
		int w = (Trajectory::LENGTH)/10;
		pfnn->Xp(o+(w*0)+(i/10)) = trajectory->heights[i][0] - root_position.y;
		pfnn->Xp(o+(w*1)+(i/10)) = trajectory->heights[i][1] - root_position.y;
		pfnn->Xp(o+(w*2)+(i/10)) = trajectory->heights[i][2] - root_position.y;
	}
}

/* Update the character and trajectory from the output from PFNN */

void updateCharacter() {

	glm::vec3 root_position = glm::vec3(
	    trajectory->positions[Trajectory::LENGTH/2].x,
	    trajectory->heights[Trajectory::LENGTH/2][1],
	    trajectory->positions[Trajectory::LENGTH/2].z);

	glm::mat3 root_rotation = trajectory->rotations[Trajectory::LENGTH/2];

	/* Update Joint Positions and Velocities */
	for (int i = 0; i < Character::JOINT_NUM; i++) {
	    int opos = 8+(((Trajectory::LENGTH/2)/10)*4)+(Character::JOINT_NUM*3*0);
	    int ovel = 8+(((Trajectory::LENGTH/2)/10)*4)+(Character::JOINT_NUM*3*1);
			int orot = 8+(((Trajectory::LENGTH/2)/10)*4)+(Character::JOINT_NUM*3*2);

	    glm::vec3 pos = (root_rotation * glm::vec3(pfnn->Yp(opos+i*3+0), pfnn->Yp(opos+i*3+1), pfnn->Yp(opos+i*3+2))) + root_position;
	    glm::vec3 vel = (root_rotation * glm::vec3(pfnn->Yp(ovel+i*3+0), pfnn->Yp(ovel+i*3+1), pfnn->Yp(ovel+i*3+2)));
			glm::mat3 rot = (root_rotation * glm::toMat3(quat_exp(glm::vec3(pfnn->Yp(orot+i*3+0), pfnn->Yp(orot+i*3+1), pfnn->Yp(orot+i*3+2)))));

		/*
	    ** Blending Between the predicted positions and
	    ** the previous positions plus the velocities
	    ** smooths out the motion a bit in the case
	    ** where the two disagree with each other.
	    */

			character->joint_positions[i]  = glm::mix(character->joint_positions[i] + vel, pos, 0.5);
	    character->joint_velocities[i] = vel;
			character->joint_rotations[i]  = rot;
	}

	/* Update Phase */
	float stand_amount = powf(1.0f - trajectory->gait_stand[Trajectory::LENGTH/2], 0.25f);
	character->phase = fmod(character->phase + (stand_amount * 0.9f + 0.1f) * 2*M_PI * pfnn->Yp(3), 2*M_PI);
}

void updateTrajectory(json json_msg, int frame) {

	// TODO: Currently ignoring outputs from pfnn and taking straight from maya. test this, blending the outputs may be better

	/* Update Trajectory */
	for (int i = 0; i < Trajectory::LENGTH - 1; i++) {
	    trajectory->positions[i]  = trajectory->positions[i+1];
	    trajectory->directions[i] = trajectory->directions[i+1];
	    trajectory->rotations[i] = trajectory->rotations[i+1];
		trajectory->heights[i][0] = trajectory->heights[i+1][0];
		trajectory->heights[i][1] = trajectory->heights[i+1][1];
		trajectory->heights[i][2] = trajectory->heights[i+1][2];
	    trajectory->gait_stand[i] = trajectory->gait_stand[i+1];
	    trajectory->gait_walk[i] = trajectory->gait_walk[i+1];
	    trajectory->gait_jog[i] = trajectory->gait_jog[i+1];
	    trajectory->gait_crouch[i] = trajectory->gait_crouch[i+1];
	    trajectory->gait_jump[i] = trajectory->gait_jump[i+1];
	    trajectory->gait_bump[i] = trajectory->gait_bump[i+1];
  	}

	int anim_frames = json_msg["AnimFrames"];
	int last_index;
	if((anim_frames - frame) < Trajectory::LENGTH/2){
		last_index = anim_frames - 1;
	}
	else {
		last_index = frame + Trajectory::LENGTH/2 - 1;
	}

	/* Last Trajectory Position */
	float posx = json_msg["PathPos"][last_index][0];
	float posy = json_msg["PathHeight"][last_index][1];
	float posz = json_msg["PathPos"][last_index][1];
	trajectory->positions[Trajectory::LENGTH - 1] = glm::vec3(posx, posy, posz);

	/* Last Trajectory Direction */
	float dirx = json_msg["PathDir"][last_index][0];
	float diry = 0.0;
	float dirz = json_msg["PathDir"][last_index][1];
	trajectory->directions[Trajectory::LENGTH - 1] = glm::vec3(dirx, diry, dirz);

	/* Last Trajectory Rotation */
	trajectory->rotations[Trajectory::LENGTH - 1] = glm::mat3(glm::rotate(atan2f(
		trajectory->directions[Trajectory::LENGTH - 1].x,
		trajectory->directions[Trajectory::LENGTH - 1].z), glm::vec3(0,1,0)));

	/* Last Trajectory Heights */
	float height_r = json_msg["PathHeight"][last_index][0];
	float height_c = json_msg["PathHeight"][last_index][1];
	float height_l = json_msg["PathHeight"][last_index][2];
	trajectory->heights[Trajectory::LENGTH - 1][0] = height_r;
	trajectory->heights[Trajectory::LENGTH - 1][1] = height_c;
	trajectory->heights[Trajectory::LENGTH - 1][2] = height_l;

	float gait_index = json_msg["Gait"][last_index];
	if(gait_index == 0) {
		trajectory->gait_stand[Trajectory::LENGTH - 1]  = 1.0;
		// trajectory->gait_walk[Trajectory::LENGTH - 1] 	= 0.0;
		// trajectory->gait_jog[Trajectory::LENGTH - 1] 	  = 0.0;
		// trajectory->gait_crouch[Trajectory::LENGTH - 1] = 0.0;
		// trajectory->gait_jump[Trajectory::LENGTH - 1] 	= 0.0;
		// trajectory->gait_bump[Trajectory::LENGTH - 1] 	= 0.0;
	}
	if(gait_index == 1) {
		// trajectory->gait_stand[Trajectory::LENGTH - 1]  = 0.0;
		trajectory->gait_walk[Trajectory::LENGTH - 1] 	= 1.0;
		// trajectory->gait_jog[Trajectory::LENGTH - 1] 	  = 0.0;
		// trajectory->gait_crouch[Trajectory::LENGTH - 1] = 0.0;
		// trajectory->gait_jump[Trajectory::LENGTH - 1] 	= 0.0;
		// trajectory->gait_bump[Trajectory::LENGTH - 1] 	= 0.0;
	}
	if(gait_index == 2) {
		// trajectory->gait_stand[Trajectory::LENGTH - 1]  = 0.0;
		// trajectory->gait_walk[Trajectory::LENGTH - 1] 	= 0.0;
		trajectory->gait_jog[Trajectory::LENGTH - 1] 	  = 1.0;
		// trajectory->gait_crouch[Trajectory::LENGTH - 1] = 0.0;
		// trajectory->gait_jump[Trajectory::LENGTH - 1] 	= 0.0;
		// trajectory->gait_bump[Trajectory::LENGTH - 1] 	= 0.0;
	}
	if(gait_index == 3) {
		// trajectory->gait_stand[Trajectory::LENGTH - 1]  = 0.0;
		// trajectory->gait_walk[Trajectory::LENGTH - 1] 	= 0.0;
		// trajectory->gait_jog[Trajectory::LENGTH - 1] 	  = 0.0;
		trajectory->gait_crouch[Trajectory::LENGTH - 1] = 1.0;
		// trajectory->gait_jump[Trajectory::LENGTH - 1] 	= 0.0;
		// trajectory->gait_bump[Trajectory::LENGTH - 1] 	= 0.0;
	}
	if(gait_index == 4) {
		// trajectory->gait_stand[Trajectory::LENGTH - 1]  = 0.0;
		// trajectory->gait_walk[Trajectory::LENGTH - 1] 	= 0.0;
		// trajectory->gait_jog[Trajectory::LENGTH - 1] 	  = 0.0;
		// trajectory->gait_crouch[Trajectory::LENGTH - 1] = 0.0;
		trajectory->gait_jump[Trajectory::LENGTH - 1] 	= 1.0;
		// trajectory->gait_bump[Trajectory::LENGTH - 1] 	= 0.0;
	}
	if(gait_index == 5) {
		// trajectory->gait_stand[Trajectory::LENGTH - 1]  = 0.0;
		// trajectory->gait_walk[Trajectory::LENGTH - 1] 	= 0.0;
		// trajectory->gait_jog[Trajectory::LENGTH - 1] 	  = 0.0;
		// trajectory->gait_crouch[Trajectory::LENGTH - 1] = 0.0;
		// trajectory->gait_jump[Trajectory::LENGTH - 1] 	= 0.0;
		trajectory->gait_bump[Trajectory::LENGTH - 1] 	= 1.0;
	}
}

/* Get Relevant Info from Yp to send to Maya and JSONify */

std::string getRelevantY(int frame) {

	std::array<float, Character::JOINT_NUM*3> joint_pos;
	for (int i = 0; i < Character::JOINT_NUM; i++) {
		for( int j = 0; j < 3; j++){
			joint_pos[i*3+j] = character->joint_positions[i][j];
		}
	}

	std::array<float, Character::JOINT_NUM*9> joint_rot;
	for (int i = 0; i < Character::JOINT_NUM; i++) {
		for( int m = 0; m < 3; m++){
			for(int n = 0; n < 3; n++){
				joint_rot[i*9+3*m+n] = character->joint_rotations[i][m][n];
			}
		}
	}

	json y_json;
	y_json["JointPos"] = joint_pos;
	y_json["Frame"] = frame;
	y_json["JointRot"] = joint_rot;
	std::string y_json_str = y_json.dump();

	return y_json_str;
}

/* A separate instance of this function is called for each connection */
void processAnim(int sock) {
	int n;
	char buffer[4096];
	std::string string_msg = "";
	bool full_msg = false;

	while(!full_msg){
		bzero(buffer,4096);
		n = recv(sock,buffer,4096,0);
		if (n < 0) error("ERROR reading from socket");

		// Have to convert from char array to string, then can parse json
		for(int i = 0; i < n; i++){
			string_msg = string_msg + buffer[i];
			if(buffer[i] == '}'){
				full_msg = true;
			}
		}
	}

	json json_msg = json::parse(string_msg);

	/* Initialise character and trajectory based on input */
	initialiseCharacter(json_msg);
	initialiseTrajectory(json_msg);

	for(int f = 0; f < json_msg["AnimFrames"]; f++){
		/* Update Xp based on character and trajectory */
		inputXp();

		/* Predict next frame */
		pfnn->predict(character->phase);

		/* Update character and trajectory */
		updateCharacter();
		updateTrajectory(json_msg, f);

		/* Extract relevant Y info, JSONify */
		std::string y_out = getRelevantY(f);

		/* Send Y info */
		n = send(sock, y_out.c_str(), y_out.length(),0);
		if (n < 0) error("ERROR writing to socket");
	}

	std::cout << "Request processed.\nSending response... ";
	n = send(sock,"#",1,0);
	if (n < 0) error("ERROR writing to socket");
	std::cout << "Response sent.\n";
}

int main(int argc, char **argv) {

	/* Resources */
	std::cout << "Setting up resources...\n";

	character = new Character();
	trajectory = new Trajectory();

	pfnn = new PFNN(PFNN::MODE_CONSTANT);
	//pfnn = new PFNN(PFNN::MODE_CUBIC);
	//pfnn = new PFNN(PFNN::MODE_LINEAR);
	pfnn->load();

	reset();

	/* Networking */

	int sockfd, newsockfd, pid;
	socklen_t clilen;
	struct sockaddr_in serv_addr, cli_addr;
	int portno = 54321;

	sockfd = socket(AF_INET, SOCK_STREAM, 0);
	if (sockfd < 0)
  	error("ERROR opening socket");

	bzero((char *) &serv_addr, sizeof(serv_addr));
	serv_addr.sin_family = AF_INET;
	serv_addr.sin_port = htons(portno);
	serv_addr.sin_addr.s_addr = INADDR_ANY;
	if (bind(sockfd, (struct sockaddr *) &serv_addr,
		sizeof(serv_addr)) < 0)
    error("ERROR binding socket");

	listen(sockfd,5);
	clilen = sizeof(cli_addr);

	std::cout << "\nListening on port " << portno << "...\n";

	while(true){
		newsockfd = accept(sockfd,
						  (struct sockaddr *) &cli_addr,
						  &clilen);
		if (newsockfd < 0)
	    error("ERROR on accept");

		pid = fork();
		if (pid < 0)
			error("ERROR on fork");

		if (pid == 0){
			std::cout << "Request received.\nProcessing request... ";
			close(sockfd);
			processAnim(newsockfd);
			reset();
			std::cout << "\nListening on port " << portno << "...\n";
			exit(0);
		}
		else
			close(newsockfd);
	}

	/* Delete Resources */

	close(sockfd);
	delete character;
	delete trajectory;
	delete pfnn;

	return 0;
}
