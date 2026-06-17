#include "VocabularyBinary.hpp"
#include <opencv2/core/core.hpp>
using namespace std;

namespace {
constexpr int32_t kMaxVocabularyNodes = 10000000;
constexpr int32_t kMaxVocabularyWords = 10000000;
}

VINSLoop::Vocabulary::Vocabulary()
: nNodes(0), nodes(nullptr), nWords(0), words(nullptr) {
}

VINSLoop::Vocabulary::~Vocabulary() {
    if (nodes != nullptr) {
        delete [] nodes;
        nodes = nullptr;
    }
    
    if (words != nullptr) {
        delete [] words;
        words = nullptr;
    }
}
    
void VINSLoop::Vocabulary::serialize(ofstream& stream) {
    stream.write((const char *)this, staticDataSize());
    stream.write((const char *)nodes, sizeof(Node) * nNodes);
    stream.write((const char *)words, sizeof(Word) * nWords);
}
    
void VINSLoop::Vocabulary::deserialize(ifstream& stream) {
    if (!stream.is_open()) {
        throw runtime_error("Could not open visual vocabulary file");
    }

    stream.read((char *)this, staticDataSize());
    if (!stream) {
        throw runtime_error("Could not read visual vocabulary header");
    }
    nodes = nullptr;
    words = nullptr;

    if (nNodes <= 0 || nWords <= 0 ||
        nNodes > kMaxVocabularyNodes || nWords > kMaxVocabularyWords) {
        throw runtime_error("Invalid visual vocabulary size in binary file");
    }
    
    nodes = new Node[nNodes];
    stream.read((char *)nodes, sizeof(Node) * nNodes);
    if (!stream) {
        throw runtime_error("Could not read visual vocabulary nodes");
    }
    
    words = new Word[nWords];
    stream.read((char *)words, sizeof(Word) * nWords);
    if (!stream) {
        throw runtime_error("Could not read visual vocabulary words");
    }
}
