function watch(obj, name) {
    return new Proxy(obj, {
        get: function (target, property, receiver) {
            try {
                if (typeof target[property] === "function") {
                    console.table([{
                        'get => ': "对象 => " + `${name}` +
                        "，读取属性：" + `\`${property}\`` +
                        "，值为：" + '`function`' +
                        "，类型为：" + (typeof target[property])
                    }]);
                } else {
                    console.table([{
                        'get => ': "对象 => " + `${name}` +
                        "，读取属性：" + `\`${property}\`` +
                        "，值为：" + `\`${target[property]}\`` +
                        "，类型为：" + (typeof target[property])
                    }]);
                }
            } catch (e) {}

            return target[property];
        },

        set: (target, property, newValue, receiver) => {
            try {
                console.table([{
                    'set => ': "对象 => " + `${name}` +
                    "，设置属性：" + `\`${property}\`` +
                    "，值为：" + `\`${newValue}\`` +
                    "，类型为：" + (typeof newValue)
                }]);
            } catch (e) {}

            return Reflect.set(target, property, newValue, receiver);
        }
    });
}


require('./rs.js')