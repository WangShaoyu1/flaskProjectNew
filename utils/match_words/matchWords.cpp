#include <iostream>
#include <vector>
#include <string>
#include <algorithm>
#include <random>
#include <sstream>
#include <QFile>
#include <QTextStream>
#include <QString>
#include <QStringList>

// 判断两个字符串的相似度
bool isSimilar(const std::string& word1, const std::string& word2, float threshold = 0.8) {
    size_t len1 = word1.size();
    size_t len2 = word2.size();
    size_t matches = 0;

    for (size_t i = 0; i < std::min(len1, len2); ++i) {
        if (tolower(word1[i]) == tolower(word2[i])) {
            ++matches;
        }
    }
    float ratio = static_cast<float>(matches) / std::max(len1, len2);
    return ratio >= threshold;
}

// 分词函数：按标点和空格分割
std::vector<std::string> tokenize(const std::string& input) {
    std::vector<std::string> tokens;
    std::string token;
    std::istringstream tokenStream(input);
    while (std::getline(tokenStream, token, ' ')) {
        tokens.push_back(token);
    }
    return tokens;
}

// 判断是否是肯定表达
bool matchPositive(const std::string& inputText, const std::vector<std::string>& positiveWords) {
    auto tokens = tokenize(inputText);

    // 完全匹配和大小写无关匹配
    for (const std::string& token : tokens) {
        for (const std::string& word : positiveWords) {
            if (strcasecmp(token.c_str(), word.c_str()) == 0) {
                return true;
            }
        }
    }

    // 模糊匹配
    for (const std::string& token : tokens) {
        for (const std::string& word : positiveWords) {
            if (isSimilar(token, word)) {
                return true;
            }
        }
    }
    return false;
}

// 分类函数
std::string classifyResponse(const std::string& inputText, const std::vector<std::string>& positiveWords) {
    return matchPositive(inputText, positiveWords) ? "肯定" : "否定";
}

// 生成上下文变化的句子
std::string addLengthVariation(const std::string& phrase) {
    std::vector<std::string> contexts = {
        "我觉得可以这样：", "确认一下，我说的是：", "实际上是这样的：", "现在我们可以这样处理：", "听我的：",
        "对了，还有：", "可以确认，现在开始：", "简单来说：", "如果你问我的话：", "具体情况是这样的："
    };

    if (rand() % 2 == 0) {  // 随机增加上下文
        return contexts[rand() % contexts.size()] + phrase;
    }
    return phrase;
}

// 主要功能封装为函数
std::vector<std::pair<std::string, std::string>> microwaveTestPipeline() {
    // 定义肯定词汇
    std::vector<std::string> positiveWords = {
        "要", "需要", "是", "好的", "好吧", "行", "成", "确定", "确认", "可以", "当然", "OK",
        "YES", "启动", "开始", "启动烹饪", "继续", "妥", "安排", "直接开始", "马上", "运行"
    };

    // 定义测试数据
    std::vector<std::string> positivePhrases = {
        "好的，开始吧", "启动烹饪", "是的，马上开始", "确认开始", "当然启动", "可以，现在就运行",
        "搞起来，启动吧", "OK，启动烹饪", "来吧，启动", "准备好了，开始吧", "直接运行吧", "启动吧"
    };

    std::vector<std::string> negativePhrases = {
        "不了，不用了", "我还没准备好", "先等等吧", "不用启动", "暂时先别开始", "不需要烹饪", "取消吧",
        "我不想启动", "这个就先算了", "不开始", "等会再启动", "暂时不要", "不用搞", "否定，不启动"
    };

    // 合并正向和负向数据
    std::vector<std::string> allPhrases = positivePhrases;
    allPhrases.insert(allPhrases.end(), negativePhrases.begin(), negativePhrases.end());

    // 生成300条测试句子
    std::vector<std::string> testSentences;
    for (size_t i = 0; i < 300; ++i) {
        testSentences.push_back(addLengthVariation(allPhrases[rand() % allPhrases.size()]));
    }

    // 分类每一句测试句子
    std::vector<std::pair<std::string, std::string>> results;
    for (const auto& sentence : testSentences) {
        results.emplace_back(sentence, classifyResponse(sentence, positiveWords));
    }

    // 保存到文件
    QFile file("microwave_test_sentences_combined.txt");
    if (file.open(QIODevice::WriteOnly | QIODevice::Text)) {
        QTextStream out(&file);
        for (const auto& result : results) {
            out << QString::fromStdString(result.first) << " => " << QString::fromStdString(result.second) << "\n";
        }
        file.close();
    }

    return results;
}

// 主程序
int main() {
    // 调用封装的函数
    auto results = microwaveTestPipeline();

    // 打印部分结果
    for (size_t i = 0; i < 10; ++i) {
        std::cout << "输入: " << results[i].first << " => 分类: " << results[i].second << std::endl;
    }

    std::cout << "测试完成，结果已保存到文件 'microwave_test_sentences_combined.txt'。" << std::endl;

    return 0;
}