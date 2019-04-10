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
    // std::cout << "Yp" << "\n";
    // std::cout << Yp << "\n";
  }

};

static PFNN* pfnn = NULL;

/* Character */

struct Character {

  enum { JOINT_NUM = 31 };

  float phase;

  glm::vec3 joint_positions[JOINT_NUM];
  glm::vec3 joint_velocities[JOINT_NUM];
	glm::mat3 joint_rotations[JOINT_NUM];

	Character()
    : phase(0) {}

};

static Character* character = NULL;

/* Trajectory */

struct Trajectory {

  enum { LENGTH = 12 };

  float width;

  glm::vec3 positions[LENGTH];
  glm::vec3 directions[LENGTH];
  glm::mat3 rotations[LENGTH];
  float heights[LENGTH];

  float gait_stand[LENGTH];
  float gait_walk[LENGTH];
  float gait_jog[LENGTH];
  float gait_crouch[LENGTH];
  float gait_jump[LENGTH];
  float gait_bump[LENGTH];

  glm::vec3 target_dir, target_vel;

  Trajectory()
    : width(25)
    , target_dir(glm::vec3(0,0,1))
    , target_vel(glm::vec3(0)) {}

};

static Trajectory* trajectory = NULL;

/* Reset */

static void reset() {

  ArrayXf Yp = pfnn->Ymean;

	glm::vec3 root_position = glm::vec3(0,0,0);
  glm::mat3 root_rotation = glm::mat3();

  for (int i = 0; i < Trajectory::LENGTH; i++) {
    trajectory->positions[i] = root_position;
    trajectory->rotations[i] = root_rotation;
    trajectory->directions[i] = glm::vec3(0,0,1);
    trajectory->heights[i] = root_position.y;
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

/* Gets Relevant Info from Yp to send to Maya */

std::string getRelevantYJson(int frame) {
	float root_xform_x_vel	 = pfnn->Yp(0);
	float root_xform_z_vel 	 = pfnn->Yp(1);
	float root_xform_ang_vel = pfnn->Yp(2);

	std::array<float, Character::JOINT_NUM*3> joint_pos;
	for (int i = 0; i < Character::JOINT_NUM*3; i++) {
		joint_pos[i] = pfnn->Yp(32+i);
	}

	json y_json;
	y_json["RootX"] = root_xform_x_vel;
	y_json["RootZ"] = root_xform_z_vel;
	y_json["RootAng"] = root_xform_ang_vel;
	y_json["JointPos"] = joint_pos;
	y_json["Frame"] = frame;

	std::string y_json_str;
	y_json_str = y_json.dump();

	return y_json_str;
}

void initialiseState(json json_msg) {

	/* Initialise Trajectory Positions */
	for(int i = 0; i < Trajectory::LENGTH; i++){
		float x = json_msg["X"][Trajectory::LENGTH*0 + i];
		float y = json_msg["X"][Trajectory::LENGTH*11 + Character::JOINT_NUM*6 + i];
		float z = json_msg["X"][Trajectory::LENGTH*1 + i];
		trajectory->positions[i] = glm::vec3(x, y, z);
	}

	/* Initialise Trajectory Rotations */
	// TODO

	/* Initialise Trajectory Directions */
	for(int i = 0; i < Trajectory::LENGTH; i++){
		float x = json_msg["X"][Trajectory::LENGTH*2 + i];
		float y = 0.0;																			//TODO: hardcoded?
		float z = json_msg["X"][Trajectory::LENGTH*3 + i];
		trajectory->directions[i] = glm::vec3(x, y, z);
	}

	/* Initialise Gait */
	for(int i = 0; i < Trajectory::LENGTH; i++){
		trajectory->gait_stand[i]  = json_msg["X"][Trajectory::LENGTH*4 + i];
		trajectory->gait_walk[i] 	 = json_msg["X"][Trajectory::LENGTH*5 + i];
		trajectory->gait_jog[i] 	 = json_msg["X"][Trajectory::LENGTH*6 + i];
		trajectory->gait_crouch[i] = json_msg["X"][Trajectory::LENGTH*7 + i];
		trajectory->gait_jump[i] 	 = json_msg["X"][Trajectory::LENGTH*8 + i];
		trajectory->gait_bump[i] 	 = json_msg["X"][Trajectory::LENGTH*9 + i];
	}

	/* Initialise Joint Positions */
	for(int i = 0; i < Character::JOINT_NUM; i++){
		float x = json_msg["X"][Trajectory::LENGTH + i*3 + 0];
		float y = json_msg["X"][Trajectory::LENGTH + i*3 + 1];
		float z = json_msg["X"][Trajectory::LENGTH + i*3 + 2];
		character->joint_positions[i] = glm::vec3(x, y, z);
	}

	/* Initialise Joint Velocities */
	for(int i = 0; i < Character::JOINT_NUM; i++){
		float x = json_msg["X"][Trajectory::LENGTH + Character::JOINT_NUM*3 + i*3 + 0];
		float y = json_msg["X"][Trajectory::LENGTH + Character::JOINT_NUM*3 + i*3 + 1];
		float z = json_msg["X"][Trajectory::LENGTH + Character::JOINT_NUM*3 + i*3 + 2];
		character->joint_velocities[i] = glm::vec3(x, y, z);
	}

	/* Initialise Trajectory Heights */
	for(int i = 0; i < Trajectory::LENGTH; i++){
		trajectory->heights[i] = json_msg["X"][Trajectory::LENGTH*11 + Character::JOINT_NUM*6 + i];
	}
}


/* */

void updateState(json json_msg) {
	/* Update Trajectory Positions */

	/* Update Trajectory Directions */

	/* Update Gait */

	/* Update Joint Positions */

	/* Update Joint Velocities */

	/* Update Trajectory Heights */

	/* Update Phase */
}

/* A separate instance of this function is called for each connection */
void processAnim(int sock) {
	int n;
	char buffer[4096];
	std::string string_msg = "";
	bool full_msg = false;

	// Deals with google compute engine problem where message not all received in one packet
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

	// std::cout << string_msg << "\n";

	/* Update Xp based on input */
	json json_msg = json::parse(string_msg);
	std::array<float, PFNN::XDIM> x_in = json_msg["X"];
	for (int i = 0; i < PFNN::XDIM; i++){
		pfnn->Xp(i) = x_in[i];
	}

	/* Update character and trajectory based on input */
	initialiseState(json_msg);

	for(int f = 0; f < json_msg["AnimFrames"]; f++){
		/* Predict next frame */
		pfnn->predict(character->phase);

		/* Extract relevant Y info, JSONify */
		std::string y_out = getRelevantYJson(f);

		/* Send y info */
		n = send(sock, y_out.c_str(), y_out.length(),0);
		if (n < 0) error("ERROR writing to socket");

		/* Update Xp, character and trajectory */
		updateState(json_msg);
	}

}

int main(int argc, char **argv) {

	/* Resources */

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
    error("ERROR on binding");

	listen(sockfd,5);
	clilen = sizeof(cli_addr);

	std::cout << "Listening...\n";

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
			close(sockfd);
			processAnim(newsockfd);
			reset();
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
