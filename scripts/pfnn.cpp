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

/* Error function for networking */
void error(const char *msg) {
	perror(msg);
	exit(1);
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
    std::cout << "Yp" << "\n";
    std::cout << Yp << "\n";
  }

};

static PFNN* pfnn = NULL;

/* A separate instance of this function is called for each connection */
void dostuff(int sock) {
	int n;
	char buffer[4000];

	bzero(buffer,4000);
	n = read(sock,buffer,3999);
	if (n < 0) error("ERROR reading from socket");

	// Have to convert from char array to string, then can parse to json
	std::string string_msg = buffer;
	json json_msg = json::parse(string_msg);
	std::array<int, 3> test = json_msg["test"];
  std::array<float, 342> data = json_msg["data"];

  for (int i = 0; i < 342; i++){
    pfnn->Xp(i) = data[i];
  }

  // pfnn->predict(character->phase);
  pfnn->predict(0);

	n = write(sock,"I got your message",18);
	if (n < 0) error("ERROR writing to socket");
}

int main(int argc, char **argv) {

  /* Create and initialise PFNN */
  pfnn = new PFNN(PFNN::MODE_CONSTANT);
  //pfnn = new PFNN(PFNN::MODE_CUBIC);
  //pfnn = new PFNN(PFNN::MODE_LINEAR);
  pfnn->load();


  /* Networking */
  int sockfd, newsockfd, portno, pid;
	socklen_t clilen;
	struct sockaddr_in serv_addr, cli_addr;

	if (argc < 2) {
		fprintf(stderr,"ERROR, no port provided\n");
 		exit(1);
	}

	sockfd = socket(AF_INET, SOCK_STREAM, 0);		//Or AF_UNIX
	if (sockfd < 0)
  	error("ERROR opening socket");

	bzero((char *) &serv_addr, sizeof(serv_addr));
	portno = atoi(argv[1]);
	serv_addr.sin_family = AF_INET;
	serv_addr.sin_port = htons(portno);
	serv_addr.sin_addr.s_addr = INADDR_ANY;
	if (bind(sockfd, (struct sockaddr *) &serv_addr,
		sizeof(serv_addr)) < 0)
    error("ERROR on binding");

	listen(sockfd,5);
	clilen = sizeof(cli_addr);

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
			dostuff(newsockfd);
			exit(0);
		}
		else
			close(newsockfd);
	}


  /* Delete Resources */
  close(sockfd);
  delete pfnn;

  return 0;
}
