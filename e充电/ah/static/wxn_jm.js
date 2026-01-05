// 引入sm-crypto库
const smCrypto = require('sm-crypto');
const sm3 = require('sm-crypto').sm3;

const key = "1E5A3925017B5845DF475B030CC393AA";
const iv = "AEC619E4D414A505BA56488343AD0407";

function wxn_post_data(post_data){
    post_data = JSON.stringify(post_data)
    const plaintext = post_data;
    const encryptedData = smCrypto.sm4.encrypt(
        plaintext,
        key,
        {
            mode: 'cbc',
            iv: iv
        }
    );
    return encryptedData
    // console.log("加密后的结果:", encryptedData);
}

// a = 'd294207f91a532c9734ae14b655caf89598a8b56aaa5c6bcd5fda7fbe619be1cf9e54baa608307882bfeca54bceb8b5a0ea51241c3edb692a1d59c9374108bfac64b2cd6726b88cb02e9ad582ba28e36946ff77d51e33dbba028e112574a8845a813c12cfd033002c5a9b100731b15026768bbe1dff3da63f144c78c29fccf69'
// wxn_decry_data(a)

// wxn_post_data({"current":6,"size":10,"areaCode":"3401","sortRules":1,"radius":"","stationLng":"117.227239","stationLat":"31.820586"})

function wxn_decry_data(encry_data) {
    const decryptedData = smCrypto.sm4.decrypt(
        encryptedData = encry_data,
        key,
        {
            mode: 'cbc',
            iv: iv
        }
    );
    return decryptedData
    // console.log("解密后的结果:", decryptedData);
}
// a = '75decb8dbd9e23e9377a9d443634f8a2f48de37e7ee2af651500b9ac195f49d1f5e61341418329fdcc2a4a7d402167e13732a37e503075d7225c75c0b8f7e4be1474b24a637fdcfd50fd095e9b12fe4a70be4e197ab6797857c7d87b4ef6f719'
// wxn_decry_data(a)





function get_sig_sm3(eny_data) {
// 要进行哈希计算的数据，可以是字符串等类型
    const data = "YYDjjkbLdNmdSK/6UMYHzQ==" + eny_data
    // 将数据转换为合适的格式，比如如果是字符串转为Buffer类型
    const bufferData = Buffer.from(data);
    // 计算SM3哈希值
    const hashValue = sm3(bufferData);
    return hashValue
}

function get_base64ent(hashValue) {

        const bufferData2 = Buffer.from(hashValue, 'utf-8');

        // 进行Base64编码
        const base64EncodedData = bufferData2.toString('base64');
        // b = base64EncodedData
        return base64EncodedData
        // console.log("Base64编码结果:", base64EncodedData);
    }
// S = hashValue

function get_signature(data, timestamp, url){
    s = get_sig_sm3(data)
    b = get_base64ent(s)
    T = "x-recharge-device:ab8157c0-8164-484a-ace9-53423a938fa4"+ "\n" + "x-recharge-sourcetype:1"+ "\n" + "x-recharge-systemnum:8.0.5"+ "\n" + "x-recharge-timestamp:"+ timestamp +"\n" + "x-recharge-version:1.0.0"
    // console.log(T)
    // p = "/recharge-mobile/app/station/page"
    p = url
    var C = 'POST' + "\n" + b + "\n" + T + "\n" + p
    // console.log('这是C：'+ C)
    P = get_sig_sm3(C)
    // console.log(P)
    signature = get_base64ent(P)
    return signature
    // console.log(signature)
}
// a = '86a239c2d567b34823a8fcd5bc532b114f62c60b40ae3b959086f23f4fd782d391132546d4ea5057e2087a86d6d4e263b60c8137b6a15a0b08955803d4b40365da4e7365edaf3823bebc832ccf98f315c2acb558cf3cbfa954894528b785779c61cff9c71bc497f12ac0e710e6bf65fbdea963fb1fec4bc41e532b03510735c6'
// timestamp = '1734597893659'
// url = '/recharge-mobile/app/station/page'
// get_signature(a, timestamp, url)
