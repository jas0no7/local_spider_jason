window = global;
//什么是eval函数
//比如 :
function add(a,b){return a+b}
//console.log(add(1,2)) //3

//现在可以用window.eval("")将其保护起来
window.eval("function add2(a,b){return a+b}")
console.log(add2(1,2)) //3
//然后可以将字符串中的函数进行混淆
