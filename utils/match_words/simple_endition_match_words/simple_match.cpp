#include <iostream>
#include <fstream>
#include <vector>
#include <regex>
#include <algorithm>
#include <string>
#include <sstream>
#include <cctype>
#include <unordered_set>
#include <locale>
#include <codecvt>
//#include <Windows.h>
#include <cwctype>

// 使用标准命名空间
using namespace std;

//定义肯定词和否定词
vector<wstring> affirmative_keywords = {
    L"是的", L"行", L"好的", L"好", L"可以", L"确认", L"对", L"没问题", L"没错", L"当然", L"需要", L"要", L"要的",
    L"没事", L"好吧", L"没关系", L"对的", L"是", L"我同意", L"行的", L"好呀", L"没问题的", L"当然可以",
    L"可以的", L"必定", L"同意", L"认同", L"完全同意", L"是这样", L"绝对", L"完全是", L"很棒", L"有的",
    L"可以吧", L"非常好", L"一切OK", L"确实", L"非常愿意", L"马上", L"立刻", L"行得通", L"我愿意", L"没错呀",
    L"确定", L"好的吧", L"完全同意", L"一切顺利", L"非常棒", L"一切都好", L"我答应", L"我同意的", L"肯定的",
    L"可以做到", L"没问题啦", L"答应", L"已经准备好", L"十分肯定", L"确实如此", L"当然愿意", L"毫无问题",
    L"好得没话说", L"一切安排妥当", L"没有问题", L"没异议", L"同意的", L"没疑问", L"没有疑虑", L"没有反对",
    L"绝对没问题", L"我全力支持", L"是的，我同意", L"愿意", L"做的好", L"好极了", L"你说的对", L"毫不犹豫",
    L"绝对支持", L"对呀", L"好像是", L"当然行", L"一切OK", L"当然可以", L"完美", L"太棒了", L"完全行",
    L"同样同意", L"就这么办", L"走吧", L"可以去做", L"完全同意", L"就这样决定", L"放心，行", L"正好",
    L"我很高兴", L"做吧", L"确认无误", L"我愿意做", L"非常好", L"顺利完成", L"是这样", L"确凿无疑", L"是的，确认",
    L"没问题啦", L"我全力支持", L"ok", L"yes", L"I agree", L"sure", L"alright", L"fine", L"perfect", L"correct",
    L"开始", L"启动", L"搞起来", L"运行"
};
vector<wstring> negative_keywords = {
    L"不", L"不能", L"不是", L"没", L"没有", L"不行", L"不做", L"不要", L"不能够", L"不想", L"不答应", L"取消", L"算逑", L"等等",
    L"等会", L"不可能", L"绝对不", L"不是的", L"不支持", L"拒绝", L"不允许", L"不可", L"无意", L"算了", L"不同意", L"不接受", L"别",
    L"不接受", L"不想做", L"不愿意", L"不赞同", L"不希望", L"不会的", L"不再", L"不管", L"不承认", L"不需要", L"不赞成", L"不想要",
    L"拒绝接受", L"没准备好", L"no", L"not", L"never", L"no way", L"I don't think so",
    L"I disagree", L"not at all", L"nope", L"can't", L"don't want", L"not possible", L"no thanks"
};

// 否定模式表达式
std::vector<std::wstring> negative_patterns = {
    LR"((不|不做|不允许|不再|不去|不可以|不希望|不想|不想做|不想要|不愿|不愿意|不接受|不是|不用|不能|不能够|不行|不要|不许|不需要|停|别|别做|拒绝|无|没有|没有|不再|没法|等会).*?(启动|继续|开始|运行|执行|进行|做|去|要|想))"
};


// 语气词和副词
std::vector<std::wstring> filler_words = {
    L"了", L"阿", L"呀", L"吧", L"的", L"嘛", L"啊", L"呢", L"就", L"可", L"总之", L"即使", L"非常", L"有点", L"其实",
	L"稍微", L"不太", L"怎么", L"因此", L"就", L"才", L"更", L"也",L"还", L"都", L"才", L"就",L"再",L"在",L"只", L"只是",L"只有"
};

// 常见的问句词汇
vector<wstring> question_words = {
    L"什么是", L"如何", L"为什么", L"怎么", L"哪里", L"谁是", L"能否", L"是否", L"有没有", L"怎样", L"什么样",
    L"哪儿", L"多大", L"什么时候", L"怎么样", L"能不能", L"几时", L"哪些", L"几何", L"要不要", L"多少", L"多么",
    L"为啥", L"如何是", L"会不会", L"是不是", L"该怎么", L"能够", L"应该", L"有没有办法", L"哪种", L"如何做",
    L"是不是", L"为什么会", L"这是什么", L"这些", L"如何理解", L"怎么做", L"为什么会这样", L"做什么", L"该如何",
    L"如何改善", L"如何解决", L"哪里可以", L"怎样才能", L"有多远", L"有多少", L"怎样才", L"怎么用", L"怎么解决", L"吗", L"么", L"呢"
};

// 对否定词与肯定词按照词汇长度排序（从长到短）
void sortByLength(std::vector<std::wstring>& keywords) {
    std::sort(keywords.begin(), keywords.end(), [](const std::wstring& a, const std::wstring& b) {
        return a.length() > b.length();
    });
}

// 函数：清理文本（去除标点符号，转换为小写，并去除填充词）
std::wstring cleanAndFilterText(const std::wstring& text, const std::unordered_set<std::wstring>& filler_words_set) {
    std::wstring cleaned_text;

    // 第一步：去除标点符号并转换为小写
    for (wchar_t ch : text) {
        if (iswalnum(ch) || iswspace(ch)) { // 保留字母、数字和空格
            cleaned_text += towlower(ch);
        }
    }

    // 第二步：去除语气词和副词
    wstringstream iss(cleaned_text);
    wstringstream oss;
    wstring word;

    while (iss >> word) { // 从文本中逐个提取单词
        if (filler_words_set.find(word) == filler_words_set.end()) { // 保留不在填充词集合中的单词
            oss << word << L" ";
        }
    }

    std::wstring result = oss.str();
    if (!result.empty()) {
        result.pop_back(); // 去除末尾多余的空格
    }

    return result;
}

void printMatches(const std::vector<std::pair<std::wstring, size_t>>& matches, const std::wstring& match_type) {
    std::wcout << match_type << ": [";
    for (const auto& match : matches) {
        std::wcout << "{Word: " << match.first << ", Position: " << match.second << "}, ";
    }
    std::wcout << "]" << std::endl;
}

// 核心处理函数
wstring simple_match(wstring text) {
    // 第一步：初始化、文本清洗
    sortByLength(affirmative_keywords); //肯定词、否定词，文本排序
    sortByLength(negative_keywords);

    // 将填充词转换为 unordered_set 以提高查找效率，清理文本
    unordered_set<std::wstring> filler_words_set(filler_words.begin(), filler_words.end());
    wstring cleaned_text = cleanAndFilterText(text, filler_words_set);

    std::wcout << "Cleaned text: " << cleaned_text << std::endl;

    // 第二步：判断是否为疑问句
    for (wstring question_word : question_words) {
        if (cleaned_text.find(question_word) != wstring::npos) {
            return L"未确定";
        }
    }

    // 保存匹配到的肯定词和否定词
    vector<pair<wstring, size_t>> affirmative_matches;
    vector<pair<wstring, size_t>> negative_matches;

    // 第三步：使用否定表达式匹配
    for (const auto& pattern : negative_patterns) {
        std::wregex re(pattern);
        std::wsmatch match;
        if (std::regex_search(cleaned_text, match, re)) {
            negative_matches.emplace_back(match.str(), match.position());
            cleaned_text.replace(match.position(), match.length(), std::wstring(match.length(), L'*'));
        }
    }

    // 第四步：匹配否定词
    for (const auto& word : negative_keywords) {
        size_t pos = cleaned_text.find(word);
        if (pos != wstring::npos) {
            negative_matches.emplace_back(word, pos);
            cleaned_text.replace(pos, word.length(), wstring(word.length(), L'*'));  // 用 * 替代
        }
    }

    // 第五步：匹配肯定词
    for (const auto& word : affirmative_keywords) {
        size_t pos = cleaned_text.find(word);
        if (pos != wstring::npos) {
            affirmative_matches.emplace_back(word, pos);
            cleaned_text.replace(pos, word.length(), wstring(word.length(), L'*'));  // 用 * 替代
        }
    }
    std::wcout << "Last Cleaned text: " << cleaned_text << std::endl;
    printMatches(affirmative_matches, L"affirmative_matches");
    printMatches(negative_matches, L"negative_matches");

    // 第六步：根据匹配结果，做最终判断
    if (!affirmative_matches.empty() && !negative_matches.empty()) {
        // 第6.1步：获取肯定和否定词在句子中的位置，最大位置如果肯定在后，则整个句子表达为肯定；反之亦然；初始化最大位置
        int affirmative_position = 0, negative_position = 0;
		wstring affirmative_max_match, negative_max_match;

		// 遍历肯定词和否定词，找到最大位置
        for (const auto& match : affirmative_matches) {
            if (match.second >= affirmative_position) {
                affirmative_position = match.second;
				affirmative_max_match = match.first;
            }
        }
        for (const auto& match : negative_matches) {
            if (match.second >= negative_position) {
                negative_position = match.second;
				negative_max_match = match.first;
            }
        }
		std::wcout << "affirmative_position: " << affirmative_position << std::endl;
		std::wcout << "negative_position: " << negative_position << std::endl;
		std::wcout << "affirmative_max_match: " << affirmative_max_match << std::endl;
		std::wcout << "negative_max_match: " << negative_max_match << std::endl;

        if (affirmative_position <= negative_position) {
            return L"否定";  // 肯定在前，否定在后，返回否定
        }
        else if (negative_position + negative_max_match.length() == affirmative_position) {
            return L"否定";
        }
        else {
            return L"肯定";  // 否定在前，肯定在后，返回肯定
        }
    }
    else if (!affirmative_matches.empty() && negative_matches.empty()) {
        if (affirmative_matches.size() == 1 && affirmative_matches[0].first.size() == 1 && cleaned_text.size() >= 5) {
            return L"未确定";
        }
        return L"肯定";
    }
    else if (affirmative_matches.empty() && !negative_matches.empty()) {
        return L"否定";
    }
    else {
        return L"未确定";
    }

    return L"未确定";
}

// 封装文件处理的函数
void processFile(const std::string& input_file, const std::string& output_file) {
    // 设置全局 UTF-8 编码
    std::locale::global(std::locale("en_US.UTF-8"));

    // 打开输入文件
    std::wifstream infile(input_file);
    infile.imbue(std::locale(std::locale(), new std::codecvt_utf8<wchar_t>));
    if (!infile.is_open()) {
        std::cerr << "无法打开输入文件: " << input_file << std::endl;
        return;
    }

    // 打开输出文件
    std::wofstream outfile(output_file);
    outfile.imbue(std::locale(std::locale(), new std::codecvt_utf8<wchar_t>));
    if (!outfile.is_open()) {
        std::cerr << "无法打开输出文件: " << output_file << std::endl;
        return;
    }

    // 逐行读取输入文件，处理每一行并写入输出文件
    std::wstring line;
    int line_number = 0;
    while (std::getline(infile, line)) {
        line_number++;

        // 跳过空行
        if (line.empty()) continue;

        // 打印当前行到控制台（可选）
        std::wcout << L"第 " << line_number << L" 行: " << line << std::endl;


        // 调用核心逻辑处理每一行文本
        std::wstring result = simple_match(line);

        // 写入输出文件
        outfile << L"输入: " << line << L" -> 结果: " << result << std::endl;
    }

    // 关闭文件
    infile.close();
    outfile.close();

    std::cout << "处理完成，结果已保存到: " << output_file << std::endl;


}
int main() {
    // 设置控制台为 UTF-8 模式
    //SetConsoleOutputCP(CP_UTF8);
    // 输入文件路径和输出文件路径
    std::string input_file = "test_sentences.txt";
    std::string output_file = "test_results_c++.txt";
    std::string test_file = "test.txt";
    // 调用文件处理函数
    processFile(input_file, output_file);

    return 0;
}