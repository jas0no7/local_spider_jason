const originalLog = Function.prototype.call.bind(console.log);


const v_log = function (...args) {
    // 使用原始引用直接调用，跳过可能被修改的 console.log
    // return originalLog(console, ...args);
};

Window = function Window(){}

for (let name in global){
    switch(name){
        case "Window":
            continue;
        case "global":
            continue;
    }
    Window.prototype[name] = global[name];
    delete global[name]
}

//代理器
const myProxy = function myProxy(obj, name) {

    const myProxy_flag = 1

    const keyToString = function keyToString(propkey) {
        return typeof propkey === 'symbol' ? `[${propkey.toString().replace('Symbol(', '').replace(')', '')}]` : propkey;
    }

    // 辅助函数：处理属性值的序列化
    const serializeValue = function serializeValue(value, visited = new WeakSet()) {
        if (typeof value === 'symbol') {
            return value.toString().replace('Symbol(', '').replace(')', '');
        }
        if (typeof value === 'function') {
            const funcName = value.name || 'anonymous';
            return `[Function: ${funcName}]`;
        }
        if (typeof value === 'object' && value !== null) {
            if (visited.has(value)) {
                return '[Circular Reference]';
            }
            visited.add(value);
            const parts = [];
            Reflect.ownKeys(value).forEach((key) => {
                const keyStr = keyToString(key);
                const val = value[key];
                const serializedVal = serializeValue(val, visited);
                parts.push(`${JSON.stringify(keyStr)}:${serializedVal}`);
            });
            return `{${parts.join(',')}}`;
        }
        if (typeof value === 'number' || typeof value === 'boolean' || value === null) {
            return JSON.stringify(value);
        }
        if (typeof value === 'string') {
            return `"${value}"`;
        }
        return JSON.stringify(value);
    }

    const my_Proxy = function my_Proxy(obj, name) {
        if (myProxy_flag) {
            return new Proxy(obj, {
                defineProperty(target, propkey, propDesc) {
                    const keyStr = keyToString(propkey);
                    // 确保 propDesc 是有效的属性描述符对象
                    if (typeof propDesc !== 'object' || propDesc === null) {
                        console.warn(`${name} -> 定义属性时，属性描述符无效`);
                        return false;
                    }
                    const result = Reflect.defineProperty(target, propkey, propDesc);
                    const valueToLog = serializeValue(propDesc);
                    v_log(`${name} -> 定义了属性 ${keyStr}  值为 -> ${valueToLog}`);
                    return result;
                },
                deleteProperty(target, propkey) {
                    const keyStr = keyToString(propkey);
                    const result = Reflect.deleteProperty(target, propkey);
                    v_log(`对象 ${name} -> 删除了属性 ${keyStr}`);
                    return result;
                },
                // 其他拦截器方法保持不变
                get(target, propkey, receiver) {
                    const keyStr = keyToString(propkey);
                    const value = Reflect.get(target, propkey, receiver);
                    const valueToLog = serializeValue(value);
                    if (!Reflect.has(target, propkey)) {
                        v_log(`${name} -> 获取了属性 [${keyStr}]  值为 -> ${valueToLog} 该属性不存在`);
                    } else {
                        v_log(`${name} -> 获取了属性 [${keyStr}]  值为 -> ${valueToLog} 存在该属性`)
                    }
                    ;
                    if (typeof value === 'object' && value !== null) {
                        return my_Proxy(value, `${name} --> ${keyStr}`);
                    }
                    return value;
                },
                set(target, propkey, value, receiver) {
                    const keyStr = keyToString(propkey);
                    const result = Reflect.set(target, propkey, value, receiver);
                    const valueToLog = serializeValue(value);
                    v_log(`${name} -> 设置了属性 ${keyStr}  值为 -> ${valueToLog}`);
                    return result;
                },
                has(target, propkey) {
                    const keyStr = keyToString(propkey);
                    const result = Reflect.has(target, propkey);
                    v_log(`${name} -> 是否拥有属性 ${keyStr} -> ${result}`);
                    return result;
                },
                ownKeys(target) {
                    const keys = Reflect.ownKeys(target);
                    v_log(`${name} -> 获取了自身所有属性 -> ${keys.map(keyToString)}`);
                    return keys;
                },
                getOwnPropertyDescriptor(target, propkey) {
                    const keyStr = keyToString(propkey);
                    const descriptor = Reflect.getOwnPropertyDescriptor(target, propkey);
                    const valueToLog = serializeValue(descriptor);
                    if (!descriptor) {
                        v_log(`${name} -> 获取私有属性 ${keyStr} 的描述为 -> ${valueToLog} 该属性非私有或不存在`);
                    } else {
                        v_log(`${name} -> 获取私有属性 ${keyStr} 的描述为 -> ${valueToLog} 该私有属性存在`);
                    }
                    return descriptor;
                },
                preventExtensions(target) {
                    const result = Reflect.preventExtensions(target);
                    v_log(`${name} -> 被设置为不可添加属性`);
                    return result;
                },
                getPrototypeOf(target) {
                    const prototype = Reflect.getPrototypeOf(target);
                    const prototypeToLog = serializeValue(prototype)
                    if (prototype) {
                        v_log(`获取了 ${name} 对象的原型, 值为${prototypeToLog} 该原型存在`);
                    } else {
                        v_log(`获取了 ${name} 对象的原型, 值为${prototypeToLog} 该原型不存在`);
                    }
                    return prototype;
                },
                isExtensible(target) {
                    const result = Reflect.isExtensible(target);
                    v_log(`对象 ${name} 允许添加新的属性`);
                    return result;
                },
                setPrototypeOf(target, proto) {
                    const result = Reflect.setPrototypeOf(target, proto);
                    const valueToLog = serializeValue(proto);
                    v_log(`对象 ${name} 将 ${valueToLog} 设为原型`);
                    return result;
                },
                apply(target, object, args) {
                    if (object === null || object === undefined) {
                        console.warn(`调用 ${target.name} 方法时，上下文对象为 ${object}`);
                    }
                    const result = Reflect.apply(target, object, args);
                    const newArgs = args.map(val => serializeValue(val));
                    v_log(`正在运行apply的对象 ${serializeValue(object)} 调用了 ${target.name || 'anonymous'} 方法 并传入了 [${newArgs}] 参数 返回的结果为${result}`);
                    return result;
                },
                construct(target, args) {
                    const instance = Reflect.construct(target, args);
                    const serializedArgs = args.map(serializeValue);
                    v_log(
                        `正在创建构造函数 ${target.name || '匿名构造函数'} 的实例 传入了 ${serializedArgs.length ? serializedArgs.join(', ') : '无'} 参数 结果为 ${instance}`
                    );
                    return instance;
                }
            });
        } else {
            return obj
        }
    }

    return my_Proxy(obj, name)
}

const safeFunction = function safeFunction(func) {
    //处理安全函数
    Function.prototype.$call = Function.prototype.call;
    const $toString = Function.toString;
    const myFunction_toString_symbol = Symbol('('.concat('', ')'));

    const myToString = function myToString() {
        return typeof this === 'function' && this[myFunction_toString_symbol] || $toString.$call(this);
    }

    const set_native = function set_native(func, key, value) {
        Object.defineProperty(func, key, {
            "enumerable": false,
            "configurable": true,
            "writable": true,
            "value": value
        });
    }

    delete Function.prototype['toString'];
    set_native(Function.prototype, "toString", myToString);
    set_native(Function.prototype.toString, myFunction_toString_symbol, "function toString() { [native code] }");

    const safe_Function = function safe_Function(func) {
        set_native(func, myFunction_toString_symbol, "function" + (func.name ? " " + func.name : "") + "() { [native code] }");
    }

    return safe_Function(func)
}

//创建函数
const makeFunction = function makeFunction(name) {
    // 使用 Function 保留函数名
    let func = new Function("v_log", `
        return function ${name}() {
            v_log('函数${name}传参-->', arguments);
        };
    `)(v_log); // 传递 v_log 到动态函数

    safeFunction(func);
    func.prototype = myProxy(func.prototype, `方法${name}.prototype`);

    return func;
}

window = global;
window.top = window;
window.self = window;
// require_ = require;
// delete require
// delete global
// delete Buffer
// delete process
// delete __dirname
// delete __filename

require('./content.js')

window.DOMParser = makeFunction('DOMParser');
window.addEventListener = makeFunction('addEventListener');
window.XMLHttpRequest = makeFunction('XMLHttpRequest');
// window.attachEvent = undefined;
window.ActiveXObject = undefined;
window.name = '';
window.indexedDB = {};



Window.prototype = myProxy(Window.prototype, 'window');
Object.setPrototypeOf(window, Window.prototype);

Document = function Document(){}
Document.prototype.createElement = function createElement(arg){
    v_log('document.createElement==>', arg)
    if (arg === 'div'){
        div = {
            getElementsByTagName: function(arg){
                v_log('document.createElement("div").getElementsByTagName==>', arg)
                if (arg === 'i'){
                    return myProxy([], 'document.createElement("div").getElementsByTagName("i")')
                }
            },
            style: {},
            setAttribute: function(arg, val){
                v_log('document.createElement("div").setAttribute==>', arg, val)
                if (arg === 'id' && val === 'a'){
                    return myProxy({}, 'document.createElement("div").setAttribute("id", "a")')
                }
            }
        }
        return myProxy(div, 'document.createElement("div")')
    }
    if (arg === 'a'){
        return {
            "ancestorOrigins": {},
            "href": "https://gxt.gansu.gov.cn/gxt/c107573/infolist.shtml",
            "origin": "https://gxt.gansu.gov.cn",
            "protocol": "https:",
            "host": "gxt.gansu.gov.cn",
            "hostname": "gxt.gansu.gov.cn",
            "port": "",
            "pathname": "/gxt/c107573/infolist.shtml",
            "search": "",
            "hash": ""
        }
    }
    if (arg === 'form'){
        return myProxy({}, 'document.createElement("form")')
    }
}

Document.prototype.getElementsByTagName = function getElementsByTagName(arg){
    v_log('document.getElementsByTagName==>', arg)
    if (arg === 'script'){
        return myProxy([], 'document.getElementsByTagName("script")')
    }
    if (arg === 'meta'){
        return myProxy([{}, {
            getAttribute: function(arg){
                v_log('document.getElementsByTagName("meta")[1].getAttribute==>', arg)
                if (arg === 'r'){
                    return 'm'
                }
            },
            parentNode: {
                removeChild: function(obj){return obj}
            },
            content: content
        }], 'document.getElementsByTagName("meta")')
    }
    if (arg === 'base'){
        return myProxy([], 'document.getElementsByTagName("base")')
    }
}

Document.prototype.getElementById = function getElementById(arg){ 
    v_log('document.getElementById==>', arg)
}

Document.prototype.appendChild = function appendChild(obj){return obj};
Document.prototype.removeChild = function removeChild(obj){return obj};

Document.prototype.visibilityState = 'visible'
Document.prototype.cookie = 'yfx_c_g_u_id_10000005=_ck25101314101317650056850866787; yfx_f_l_v_t_10000005=f_t_1760335813763__r_t_1760335813763__v_t_1760340672420__r_c_0; 4hP44ZykCTt5P=0RevXiE2ZeU2HMZwksv_mlkD.22QEWNGpO5pVdEX8y6vVRIo2yqjXh673dqFYzlHa_AGDpwsz3w0UP5AkcsozE9lEurW80yY7R4AscTUIM.Yq4x_GHATtmI0juQX3AU6vkiMZOVu.Ma8A7Xwse.lqgQhuE7L14ZO_E260ul5Yt4ook8fznVzG.vMeNmb3YRWv4r5Q8TunZlnbUgCDZknjZ9UVybMgaWTsXraX72ubXy942svInKh2sZ2PWiwL6Qq6Te_zMfJCNwF9rZ98QcR2ca0EqMl2etqqBq7OqXoIZx.ic6YH6g2ctWibm6i16fjCRQxQiKsE7W7XxihNBZwjBa5W.6LKHFiw4R9dJ1jcLH5qUc9IA.r500tCZa6vhafuLlB4MY6HhcpzGr8iikvEOHa.Dcg8ZCUi_1Wkr_8xr69hLXE9fhazH1bvFPt4fof9'

HTMLDocument = function HTMLDocument(){}
Object.setPrototypeOf(HTMLDocument.prototype, Document.prototype)
document = new HTMLDocument()

Navigator = function Navigator(){}
navigator = {
    appCodeName: "Mozilla",
    appName: "Netscape",
    appVersion: "5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    connection: {
        downlink: 2.4,
        effectiveType: "4g",
        onchange: null,
        rtt: 50,
        saveData: false
    },
    cookieEnabled: true,
    deprecatedRunAdAuctionEnforcesKAnonymity: true,
    deviceMemory: 8,
    doNotTrack: null,
    hardwareConcurrency: 22,
    languages: ["zh-CN", "en", "zh"],
    language: "zh-CN",
    onLine: true,
    platform: "Win32",
    product: "Gecko",
    productSub: '20030107',
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    vendor: "Google Inc.",
    vendorSub: "",
    // webdriver: false,
    webkitPersistentStorage: {},
    getBattery: function () {
        return {
            then() {
            }
        }
    },
    webdriver: false
}
Object.setPrototypeOf(navigator, Navigator.prototype)

History = function History(){}
history = {}
Object.setPrototypeOf(history, History.prototype)

Location = function Location(){}
location = {
    "ancestorOrigins": {},
    "href": "https://gxt.gansu.gov.cn/gxt/c107573/infolist.shtml",
    "origin": "https://gxt.gansu.gov.cn",
    "protocol": "https:",
    "host": "gxt.gansu.gov.cn",
    "hostname": "gxt.gansu.gov.cn",
    "port": "",
    "pathname": "/gxt/c107573/infolist.shtml",
    "search": "",
    "hash": ""
}
Object.setPrototypeOf(location, Location.prototype)

Screen = function Screen(){}
screen = {}
Object.setPrototypeOf(screen, Screen.prototype)

Storage = function Storage(){}

localStorage = {
    getItem: function getItem(ss) {
        v_log("localStorage.getItem传入了参数", ss)
        return this[ss]
    },
    setItem: function setItem(aa, bb) {
        v_log("localStorage.setItem传入了参数", arguments)
        this[aa] = bb
    },
    removeItem: function removeItem(aa) {
        v_log("localStorage.removeItem传入了参数", arguments)
        delete this[aa]
    }
};
Object.setPrototypeOf(localStorage, Storage.prototype)
sessionStorage = {
    getItem: function getItem(ss) {
        v_log("sessionStorage.getItem传入了参数", ss)
        return this[ss]
    },
    setItem: function setItem(aa, bb) {
        v_log("sessionStorage.setItem传入了参数", arguments)
        this[aa] = bb
    },
    removeItem: function removeItem(aa) {
        v_log("sessionStorage.removeItem传入了参数", arguments)
        delete this[aa]
    }
};
Object.setPrototypeOf(sessionStorage, Storage.prototype)

window.setInterval = function(){};
window.setTimeout = function(){};

document = myProxy(document, 'document');
navigator = myProxy(navigator, 'navigator');
screen = myProxy(screen, 'screen');
history = myProxy(history, 'history');
location = myProxy(location, 'location');
localStorage = myProxy(localStorage, 'localStorage');
sessionStorage = myProxy(sessionStorage, 'sessionStorage');

require('./ts.js')
require('./cd.js')

function get_ck() {
    return document.cookie.split('=')[1].split(';')[0];
}

console.log(get_ck())