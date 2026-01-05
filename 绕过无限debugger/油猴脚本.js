//1 随机数
(function(){
    console.log("JS注入成功")
    let _setInterval = setInterval
    setInterval = function(func,delay){
        if (func.toString().indexOf("debugger") != -1){
            console.log("Hook setInterval debugger!");
            return function(){};
        }
        return _setInterval(func,delay);
    };
})();


// 2 window.eval()
(function() {
    console.log("油猴脚本注入成功")
    let _eval = window.eval;
    window.eval = function (string) {
        if (string.includes("debugger")) {
            console.log("Hook eval debugger!")
        }
        return  _eval(string.replace(/debugger\s*;?/g, ""));
    };
    window.eval.toString = function(){
    return _eval.toString();
    }

})();


// 3 constructor
(function () {
    console.log("油猴脚本注入成功")

    let _constructor = Function.prototype.constructor;
    Function.prototype.constructor = function (string) {
        if (string === "debugger") {
            console.log("Hook constructor debugger!");
            return function() {};
        }
        return _constructor(string);
    };
})();