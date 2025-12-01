

function watch(obj, name) {
    return new Proxy(obj, {
        get: function (target, property, receiver) {
            try {
                if (typeof target[property] === 'function') {
                    console.table(['*get => ' + '对象 => ' + `${name}` + '，' + '取属性 => ' + `${property}` + '，' + '值为:' + 'function' + '，' + '类型为:' + (typeof target[property])]);
                } else {
                    console.table(['*get => ' + '对象 => ' + `${name}` + '，' + '取属性 => ' + `${property}` + '，' + '值为:' + `${target[property]}` + '，' + '类型为:' + (typeof target[property])]);
                }
            } catch (e) {}

            return target[property];
        },

        set: (target, property, newValue, receiver) => {
            try {
                console.table(['*set => ' + '对象 => ' + `${name}` + '，' + '设置属性 => ' + `${property}` + '，' + '值为:' + `${newValue}` + '，' + '类型为:' + (typeof newValue)]);
            } catch (e) {}

            return Reflect.set(target, property, newValue, receiver);
        }
    });
}
delete _dirname
delete _filename
fn = function(){}
//window 部分
window= global;
window.top = window
window.name = '&$_YWTU=XxcPp80LG9FokOhG0ofZXHYTRNRu4iOxEvOFze_eg7g&$_YVTX=Wa&vdFm='

window.indexedDB = {}
XMLHttpRequest = fn;




//document 部分
document = {}




div = {
    getElementsByTagName :function(val){
        console.log('div.getElementsByTagName被调用了，参数是 =========>',val)
        if (div === 'i'){
            return []
            }
    }

}
document.createElement = function(val){
    console.log('document.createElement被调用了，参数是=====>',val)
    if (val === 'div'){
        return div;
        }
}
document.appendChild= function(val){
    console.log('document.appendChild被调用了，参数是=====>',val)


}
document.removeChild= function(val){
    console.log('document.removeChild被调用了，参数是=====>',val)


}
document.getElementsByTagName= function(val){

    console.log('document.getElementsByTagName被调用了，参数是=========>',val)
}





//location部分

location = {
    "ancestorOrigins": {},
    "href": "https://www.jscq.com.cn/",
    "origin": "https://www.jscq.com.cn",
    "protocol": "https:",
    "host": "www.jscq.com.cn",
    "hostname": "www.jscq.com.cn",
    "port": "",
    "pathname": "/",
    "search": "",
    "hash": ""
}

//localStorage部分

localStorage = {}
sessionStorage={}
window = watch(window,'window')

document = watch(document,'document')
location = watch(location,'location')
div = watch(div,'div')
localStorage = watch(localStorage,'localStorage')
sessionStorage= watch(sessionStorage,'sessionStorage')


require('./rs.js')


console.log(document.cookie);