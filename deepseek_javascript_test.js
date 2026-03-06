(async function testNewPageSend() {
    console.log('🔍 开始测试新页面发送...');

    // 辅助函数：等待元素出现
    function waitForElement(selector, timeout = 5000) {
        return new Promise((resolve, reject) => {
            const start = Date.now();
            const check = () => {
                const el = document.querySelector(selector);
                if (el) {
                    resolve(el);
                } else if (Date.now() - start > timeout) {
                    reject(new Error(`元素 ${selector} 超时未出现`));
                } else {
                    setTimeout(check, 200);
                }
            };
            check();
        });
    }

    try {
        // 1. 等待输入框出现
        const inputBox = await waitForElement('textarea[placeholder*="给 DeepSeek 发送消息"]');
        console.log('✅ 找到输入框');

        // 2. 聚焦并插入测试消息
        inputBox.focus();
        inputBox.select(); // 全选可能有助于清除
        const testMessage = '这是一个新页面测试消息';
        document.execCommand('insertText', false, testMessage);
        console.log('✅ 已通过 execCommand 插入消息');

        // 3. 等待按钮启用（可能 React 需要时间）
        await new Promise(r => setTimeout(r, 500));

        // 4. 等待发送按钮出现
        const sendButton = await waitForElement('div._7436101.ds-icon-button[role="button"]');
        console.log('✅ 找到发送按钮');

        // 5. 检查按钮是否启用
        if (sendButton.getAttribute('aria-disabled') === 'true') {
            console.warn('⚠️ 按钮禁用，等待启用...');
            const start = Date.now();
            while (Date.now() - start < 3000) {
                await new Promise(r => setTimeout(r, 200));
                if (sendButton.getAttribute('aria-disabled') !== 'true') break;
            }
            if (sendButton.getAttribute('aria-disabled') === 'true') {
                throw new Error('按钮超时未启用');
            }
            console.log('✅ 按钮已启用');
        } else {
            console.log('✅ 按钮已启用');
        }

        // 6. 点击发送
        sendButton.click();
        console.log('✅ 已点击发送按钮，请观察页面是否成功发送消息并开始回复');

        // 7. 检查输入框是否清空（表示可能发送成功）
        setTimeout(() => {
            if (inputBox.value === '') {
                console.log('✅ 输入框已清空，消息很可能已发送');
            } else {
                console.log('⚠️ 输入框未清空，可能发送失败');
            }
        }, 1000);

    } catch (error) {
        console.error('❌ 测试失败:', error.message);
    }
})();