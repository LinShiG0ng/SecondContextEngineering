// 上下文工程演示系统 - 前端逻辑

// 全局状态
const state = {
    messages: [],
    compressed: false,
    systemPrompts: [],
    compressionCount: 0,
    tokensSaved: 0
};

// ===== 工具函数 =====

function showLoading(text = '处理中...') {
    document.getElementById('loading-overlay').style.display = 'flex';
    document.getElementById('loading-text').textContent = text;
}

function hideLoading() {
    document.getElementById('loading-overlay').style.display = 'none';
}

function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type} show`;

    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

function estimateCost(tokens) {
    // 简化的成本估算（GPT-3.5-turbo价格）
    return (tokens / 1000 * 0.0005).toFixed(4);
}

// ===== 导入对话 =====

async function importConversation() {
    const jsonText = document.getElementById('import-json').value.trim();

    console.log('importConversation() 被调用');

    if (!jsonText) {
        showNotification('请输入JSON数据', 'warning');
        return;
    }

    try {
        showLoading('导入中...');

        const data = JSON.parse(jsonText);
        console.log('解析的JSON数据:', data);

        const response = await fetch('/api/import', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });

        console.log('导入响应状态:', response.status);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('API错误响应:', errorText);
            throw new Error(`API错误 (${response.status}): ${errorText}`);
        }

        const result = await response.json();
        console.log('导入结果:', result);

        if (result.status === 'success') {
            state.messages = data.messages;
            console.log('state.messages 已更新:', state.messages);

            // 更新界面
            updateStats(result);
            displayMessages(state.messages);

            showNotification(`导入成功: ${result.message_count} 条消息`, 'success');
        } else {
            throw new Error(result.detail || '导入失败，状态不是success');
        }

    } catch (error) {
        console.error('导入错误:', error);
        showNotification(`导入失败: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

function updateStats(result) {
    document.getElementById('message-count').textContent = result.message_count || 0;
    document.getElementById('total-tokens').textContent = result.total_tokens || 0;
    document.getElementById('system-count').textContent = result.system_prompt_count || 0;
    document.getElementById('token-usage').textContent = `${result.total_tokens || 0}/8000`;
}

function displayMessages(messages) {
    const container = document.getElementById('chat-messages');
    container.innerHTML = '';

    messages.forEach(msg => {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${msg.role}`;

        const roleSpan = document.createElement('span');
        roleSpan.className = 'role';
        roleSpan.textContent = msg.role === 'user' ? '👤 用户' :
                              msg.role === 'assistant' ? '🤖 助手' :
                              '⚙️ System';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'content';
        contentDiv.textContent = msg.content;

        msgDiv.appendChild(roleSpan);
        msgDiv.appendChild(contentDiv);
        container.appendChild(msgDiv);
    });

    container.scrollTop = container.scrollHeight;
}

// ===== 加载示例 =====

function loadExample() {
    const example = {
        "messages": [
            {"role": "system", "content": "你是一个专业的Python编程助手"},
            {"role": "user", "content": "帮我创建一个Flask项目"},
            {"role": "assistant", "content": "好的，我来帮你创建Flask项目。首先需要安装Flask库..."},
            {"role": "user", "content": "添加用户认证功能"},
            {"role": "assistant", "content": "我们可以使用Flask-Login来实现用户认证功能..."},
            {"role": "user", "content": "main.py第42行出现TypeError"},
            {"role": "assistant", "content": "这个TypeError是因为类型不匹配。让我帮你分析一下..."},
            {"role": "user", "content": "如何优化数据库查询？"},
            {"role": "assistant", "content": "优化数据库查询可以从以下几个方面入手：1. 添加索引..."},
            {"role": "user", "content": "实现一个缓存系统"},
            {"role": "assistant", "content": "我建议使用Redis作为缓存系统..."}
        ]
    };

    document.getElementById('import-json').value = JSON.stringify(example, null, 2);
    showNotification('示例已加载，点击"导入"按钮继续', 'info');
}

// ===== 执行压缩 =====

async function compress() {
    console.log('compress() 被调用');
    console.log('当前消息数量:', state.messages.length);
    console.log('当前消息:', state.messages);

    if (state.messages.length < 2) {
        showNotification('消息数量不足，无法压缩（至少需要2条）', 'warning');
        return;
    }

    try {
        showLoading('执行压缩中...');

        console.log('发送压缩请求...');

        const response = await fetch('/api/compress', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                messages: state.messages,
                force: true
            })
        });

        console.log('响应状态:', response.status);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('API错误响应:', errorText);
            throw new Error(`API错误 (${response.status}): ${errorText}`);
        }

        const result = await response.json();
        console.log('压缩结果:', result);

        if (result.status === 'success') {
            // 更新对比数据
            updateComparison(result);

            // 更新消息列表
            state.messages = result.compressed.messages;
            displayMessages(state.messages);

            // 更新统计
            state.compressionCount++;
            state.tokensSaved += result.statistics.tokens_saved;

            document.getElementById('compression-count').textContent = state.compressionCount;
            document.getElementById('tokens-saved').textContent = state.tokensSaved;

            showNotification(
                `压缩完成！节省 ${result.statistics.tokens_saved} tokens (${(result.statistics.compression_ratio * 100).toFixed(1)}%)`,
                'success'
            );
        } else {
            throw new Error(result.detail || '压缩失败，状态不是success');
        }

    } catch (error) {
        console.error('压缩错误:', error);
        showNotification(`压缩失败: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

function updateComparison(result) {
    // 压缩前
    document.getElementById('before-msg-count').textContent = result.original.message_count;
    document.getElementById('before-tokens').textContent = result.original.tokens.toLocaleString();
    document.getElementById('before-cost').textContent = `$${estimateCost(result.original.tokens)}`;

    // 压缩后
    document.getElementById('after-msg-count').textContent = result.compressed.message_count;
    document.getElementById('after-tokens').textContent = result.compressed.tokens.toLocaleString();
    document.getElementById('after-cost').textContent = `$${estimateCost(result.compressed.tokens)}`;

    // 改进效果
    document.getElementById('token-saving').textContent =
        `${(result.statistics.compression_ratio * 100).toFixed(1)}%`;
    document.getElementById('cost-reduction').textContent =
        `${(result.statistics.compression_ratio * 100).toFixed(1)}%`;
    document.getElementById('info-retention').textContent =
        `${(result.statistics.info_retention * 100).toFixed(0)}%`;
}

// ===== 导出功能 =====

async function exportJSON() {
    if (state.messages.length === 0) {
        showNotification('没有消息可导出', 'warning');
        return;
    }

    try {
        const response = await fetch('/api/export', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                messages: state.messages
            })
        });

        const result = await response.json();

        // 显示导出结果
        const output = document.getElementById('export-output');
        output.textContent = JSON.stringify(result, null, 2);

        showNotification('导出成功', 'success');

    } catch (error) {
        showNotification(`导出失败: ${error.message}`, 'error');
    }
}

async function copyToClipboard() {
    const output = document.getElementById('export-output').textContent;

    if (!output) {
        showNotification('没有内容可复制', 'warning');
        return;
    }

    try {
        await navigator.clipboard.writeText(output);
        showNotification('已复制到剪贴板', 'success');
    } catch (error) {
        showNotification('复制失败', 'error');
    }
}

// ===== 对话功能 =====

async function sendMessage() {
    const input = document.getElementById('user-input');
    const content = input.value.trim();

    if (!content) {
        return;
    }

    // 添加用户消息到界面
    state.messages.push({
        role: 'user',
        content: content
    });
    displayMessages(state.messages);

    // 清空输入框
    input.value = '';

    try {
        showLoading('AI思考中...');

        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                message: content
            })
        });

        const result = await response.json();

        if (result.status === 'success') {
            // 添加助手响应
            state.messages.push({
                role: 'assistant',
                content: result.response
            });
            displayMessages(state.messages);

            // 更新token使用率
            document.getElementById('token-usage').textContent =
                `${Math.round(result.usage_rate * 8000)}/8000`;

            // 如果触发了压缩
            if (result.compression_triggered) {
                showNotification('自动压缩已触发！', 'info');
                state.compressionCount++;
                document.getElementById('compression-count').textContent = state.compressionCount;
            }
        }

    } catch (error) {
        showNotification(`发送失败: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

// ===== 对比测试 =====

async function runComparison() {
    if (state.messages.length < 5) {
        showNotification('消息数量不足（需要至少5条）', 'warning');
        return;
    }

    const testQuery = document.getElementById('test-query').value.trim();

    if (!testQuery) {
        showNotification('请输入测试问题', 'warning');
        return;
    }

    try {
        showLoading('运行对比测试...');

        const response = await fetch('/api/compare', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                messages: state.messages,
                test_query: testQuery
            })
        });

        const result = await response.json();

        if (result.status === 'success') {
            displayComparisonResults(result);
            showNotification('对比测试完成', 'success');
        }

    } catch (error) {
        showNotification(`测试失败: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

function displayComparisonResults(result) {
    const container = document.getElementById('comparison-results');

    const html = `
        <div class="comparison-results">
            <h4>测试问题: "${document.getElementById('test-query').value}"</h4>

            <div class="result-section">
                <h5>📊 原始上下文</h5>
                <p>Tokens: ${result.original.tokens.toLocaleString()}</p>
                <p>响应时间: ${result.original.response_time.toFixed(2)}秒</p>
                <p>成本: $${result.original.cost.toFixed(4)}</p>
                <p>响应: ${result.original.response}</p>
            </div>

            <div class="result-section">
                <h5>📊 压缩上下文</h5>
                <p>Tokens: ${result.compressed.tokens.toLocaleString()}</p>
                <p>响应时间: ${result.compressed.response_time.toFixed(2)}秒</p>
                <p>成本: $${result.compressed.cost.toFixed(4)}</p>
                <p>响应: ${result.compressed.response}</p>
            </div>

            <div class="result-section improvements-section">
                <h5>✨ 效果提升</h5>
                <p>Token节省: ${result.improvements.token_reduction}</p>
                <p>速度提升: ${result.improvements.speed_increase}</p>
                <p>成本降低: ${result.improvements.cost_reduction}</p>
                <p>相似度: ${(result.improvements.similarity_score * 100).toFixed(1)}%</p>
            </div>
        </div>
    `;

    container.innerHTML = html;
}

// ===== 统计信息 =====

async function refreshStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();

        const container = document.getElementById('stats-display');
        container.innerHTML = `
            <div class="stats-info">
                <h4>💬 对话统计</h4>
                <p>总消息数: ${stats.conversation?.total_messages || 0}</p>
                <p>用户消息: ${stats.conversation?.user_messages || 0}</p>
                <p>助手消息: ${stats.conversation?.assistant_messages || 0}</p>

                <h4>🔄 压缩统计</h4>
                <p>压缩次数: ${stats.compression?.count || 0}</p>
                <p>节省Tokens: ${(stats.compression?.total_saved || 0).toLocaleString()}</p>
                <p>平均压缩率: ${((stats.compression?.avg_ratio || 0) * 100).toFixed(1)}%</p>

                <h4>🏗️ 存储统计</h4>
                <p>短期记忆: ${stats.storage?.short_term_count || 0} 条</p>
                <p>中期记忆: ${stats.storage?.mid_term_count || 0} 条</p>
            </div>
        `;

        showNotification('统计信息已更新', 'success');

    } catch (error) {
        showNotification(`刷新失败: ${error.message}`, 'error');
    }
}

// ===== 重置 =====

async function reset() {
    if (!confirm('确定要重置对话吗？')) {
        return;
    }

    try {
        await fetch('/api/reset', { method: 'POST' });

        state.messages = [];
        state.compressionCount = 0;
        state.tokensSaved = 0;

        document.getElementById('chat-messages').innerHTML = `
            <div class="welcome-message">
                <p>👋 对话已重置</p>
                <p>请导入新的对话历史或开始新对话</p>
            </div>
        `;

        document.getElementById('message-count').textContent = '0';
        document.getElementById('total-tokens').textContent = '0';
        document.getElementById('compression-count').textContent = '0';
        document.getElementById('tokens-saved').textContent = '0';

        showNotification('对话已重置', 'success');

    } catch (error) {
        showNotification(`重置失败: ${error.message}`, 'error');
    }
}

// ===== 初始化 =====

document.addEventListener('DOMContentLoaded', () => {
    console.log('上下文工程演示系统已加载');
    refreshStats();
});
