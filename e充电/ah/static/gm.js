let smCrypto = require('sm-crypto');

function sm2decrypt(encryptedData, privateKey = '04a9122a9bf5bbe30b0b29bdd5c9e35a1fb8f4f30a58fbe5daa0c92bc3930503') {
    if (typeof encryptedData === 'string' && encryptedData.startsWith('04')) {
        encryptedData = encryptedData.substring(2)
    }
    return JSON.parse(smCrypto.sm2.doDecrypt(encryptedData, privateKey, 1, {output: 'string'}));

}

// sm2 加密
function sm2encrypt(encryptData, publicKey="04539279C0082E3938382D533335858B835911471133B79505F19584D64BC556C69E5BC5DF66B12841A30A83679D8A6D501D424D9869916124E30367919A03F758") {
    return smCrypto.sm2.doEncrypt(encryptData, publicKey, 1, {output: 'string'});
}


function sm3encrypt(encryptData) {
    return smCrypto.sm3(encryptData).toUpperCase();
}


// sm4加密 不能用自带的 使用的是修改过的sm4
function SM4Util() {
    this.SM4_ENCRYPT = 1,
        this.SM4_DECRYPT = 0;
    var e = [214, 144, 233, 254, 204, 225, 61, 183, 22, 182, 20, 194, 40, 251, 44, 5, 43, 103, 154, 118, 42, 190, 4, 195, 170, 68, 19, 38, 73, 134, 6, 153, 156, 66, 80, 244, 145, 239, 152, 122, 51, 84, 11, 67, 237, 207, 172, 98, 228, 179, 28, 169, 201, 8, 232, 149, 128, 223, 148, 250, 117, 143, 63, 166, 71, 7, 167, 252, 243, 115, 23, 186, 131, 89, 60, 25, 230, 133, 79, 168, 104, 107, 129, 178, 113, 100, 218, 139, 248, 235, 15, 75, 112, 86, 157, 53, 30, 36, 14, 94, 99, 88, 209, 162, 37, 34, 124, 59, 1, 33, 120, 135, 212, 0, 70, 87, 159, 211, 39, 82, 76, 54, 2, 231, 160, 196, 200, 158, 234, 191, 138, 210, 64, 199, 56, 181, 163, 247, 242, 206, 249, 97, 21, 161, 224, 174, 93, 164, 155, 52, 26, 85, 173, 147, 50, 48, 245, 140, 177, 227, 29, 246, 226, 46, 130, 102, 202, 96, 192, 41, 35, 171, 13, 83, 78, 111, 213, 219, 55, 69, 222, 253, 142, 47, 3, 255, 106, 114, 109, 108, 91, 81, 141, 27, 175, 146, 187, 221, 188, 127, 17, 217, 92, 65, 31, 16, 90, 216, 10, 193, 49, 136, 165, 205, 123, 189, 45, 116, 208, 18, 184, 229, 180, 176, 137, 105, 151, 74, 12, 150, 119, 126, 101, 185, 241, 9, 197, 110, 198, 132, 24, 240, 125, 236, 58, 220, 77, 32, 121, 238, 95, 62, 215, 203, 57, 72]
        , r = [2746333894, 1453994832, 1736282519, 2993693404]
        , n = [462357, 472066609, 943670861, 1415275113, 1886879365, 2358483617, 2830087869, 3301692121, 3773296373, 4228057617, 404694573, 876298825, 1347903077, 1819507329, 2291111581, 2762715833, 3234320085, 3705924337, 4177462797, 337322537, 808926789, 1280531041, 1752135293, 2223739545, 2695343797, 3166948049, 3638552301, 4110090761, 269950501, 741554753, 1213159005, 1684763257];
    this.GET_ULONG_BE = function (t, e) {
        return (255 & t[e]) << 24 | (255 & t[e + 1]) << 16 | (255 & t[e + 2]) << 8 | 255 & t[e + 3]
    }
        ,
        this.PUT_ULONG_BE = function (t, e, r) {
            var n = 255 & t >> 24
                , i = 255 & t >> 16
                , o = 255 & t >> 8
                , s = 255 & t;
            e[r] = n > 128 ? n - 256 : n,
                e[r + 1] = i > 128 ? i - 256 : i,
                e[r + 2] = o > 128 ? o - 256 : o,
                e[r + 3] = s > 128 ? s - 256 : s
        }
        ,
        this.SHL = function (t, e) {
            return (4294967295 & t) << e
        }
        ,
        this.ROTL = function (t, e) {
            return this.SHL(t, e) | t >> 32 - e
        }
        ,
        this.sm4Lt = function (t) {
            var e, r = new Array(4), n = new Array(4);
            return this.PUT_ULONG_BE(t, r, 0),
                n[0] = this.sm4Sbox(r[0]),
                n[1] = this.sm4Sbox(r[1]),
                n[2] = this.sm4Sbox(r[2]),
                n[3] = this.sm4Sbox(r[3]),
            (e = this.GET_ULONG_BE(n, 0)) ^ this.ROTL(e, 2) ^ this.ROTL(e, 10) ^ this.ROTL(e, 18) ^ this.ROTL(e, 24)
        }
        ,
        this.sm4F = function (t, e, r, n, i) {
            return t ^ this.sm4Lt(e ^ r ^ n ^ i)
        }
        ,
        this.sm4CalciRK = function (t) {
            var e, r = new Array(4), n = new Array(4);
            return this.PUT_ULONG_BE(t, r, 0),
                n[0] = this.sm4Sbox(r[0]),
                n[1] = this.sm4Sbox(r[1]),
                n[2] = this.sm4Sbox(r[2]),
                n[3] = this.sm4Sbox(r[3]),
            (e = this.GET_ULONG_BE(n, 0)) ^ this.ROTL(e, 13) ^ this.ROTL(e, 23)
        }
        ,
        this.sm4Sbox = function (t) {
            var r = e[255 & t];
            return r > 128 ? r - 256 : r
        }
        ,
        this.sm4_setkey_enc = function (t, e) {
            return null == t ? (alert("ctx is null!"),
                !1) : null == e || 16 != e.length ? (alert("key error!"),
                !1) : (t.mode = this.SM4_ENCRYPT,
                void this.sm4_setkey(t.sk, e))
        }
        ,
        this.sm4_setkey = function (t, e) {
            var i = new Array(4)
                , o = new Array(36)
                , s = 0;
            for (i[0] = this.GET_ULONG_BE(e, 0),
                     i[1] = this.GET_ULONG_BE(e, 4),
                     i[2] = this.GET_ULONG_BE(e, 8),
                     i[3] = this.GET_ULONG_BE(e, 12),
                     o[0] = i[0] ^ r[0],
                     o[1] = i[1] ^ r[1],
                     o[2] = i[2] ^ r[2],
                     o[3] = i[3] ^ r[3],
                     s = 0; s < 32; s++)
                o[s + 4] = o[s] ^ this.sm4CalciRK(o[s + 1] ^ o[s + 2] ^ o[s + 3] ^ n[s]),
                    t[s] = o[s + 4]
        }
        ,
        this.padding = function (t, e) {
            if (null == t)
                return null;
            var r = null;
            if (e == this.SM4_ENCRYPT) {
                var n = parseInt(16 - t.length % 16);
                r = t.slice(0);
                for (var i = 0; i < n; i++)
                    r[t.length + i] = n
            } else {
                var o = t[t.length - 1];
                r = t.slice(0, t.length - o)
            }
            return r
        }
        ,
        this.sm4_one_round = function (t, e, r) {
            var n = 0
                , i = new Array(36);
            for (i[0] = this.GET_ULONG_BE(e, 0),
                     i[1] = this.GET_ULONG_BE(e, 4),
                     i[2] = this.GET_ULONG_BE(e, 8),
                     i[3] = this.GET_ULONG_BE(e, 12); n < 32;)
                i[n + 4] = this.sm4F(i[n], i[n + 1], i[n + 2], i[n + 3], t[n]),
                    n++;
            this.PUT_ULONG_BE(i[35], r, 0),
                this.PUT_ULONG_BE(i[34], r, 4),
                this.PUT_ULONG_BE(i[33], r, 8),
                this.PUT_ULONG_BE(i[32], r, 12)
        }
        ,
        this.sm4_crypt_ecb = function (t, e) {
            null == e && alert("input is null!"),
            t.isPadding && t.mode == this.SM4_ENCRYPT && (e = this.padding(e, this.SM4_ENCRYPT));
            for (var r = 0, n = e.length, i = new Array; n > 0; n -= 16) {
                var o = new Array(16)
                    , s = e.slice(16 * r, 16 * (r + 1));
                this.sm4_one_round(t.sk, s, o),
                    i = i.concat(o),
                    r++
            }
            var u = i;
            for (t.isPadding && t.mode == this.SM4_DECRYPT && (u = this.padding(u, this.SM4_DECRYPT)),
                     r = 0; r < u.length; r++)
                u[r] < 0 && (u[r] = u[r] + 256);
            return u
        }
        ,
        this.sm4_crypt_cbc = function (t, e, r) {
            null != e && 16 == e.length || alert("iv error!"),
            null == r && alert("input is null!"),
            t.isPadding && t.mode == this.SM4_ENCRYPT && (r = this.padding(r, this.SM4_ENCRYPT));
            var n, i = 0, o = 0, s = new Array(16), u = new Array(16), a = r.length, c = new Array;
            if (t.mode == this.SM4_ENCRYPT)
                for (; a > 0; a -= 16) {
                    for (n = r.slice(16 * o, 16 * (o + 1)),
                             i = 0; i < 16; i++)
                        s[i] = n[i] ^ e[i];
                    this.sm4_one_round(t.sk, s, u),
                        e = u.slice(0, 16),
                        c = c.concat(u),
                        o++
                }
            else
                for (var f = []; a > 0; a -= 16) {
                    for (f = (n = r.slice(16 * o, 16 * (o + 1))).slice(0, 16),
                             this.sm4_one_round(t.sk, n, s),
                             i = 0; i < 16; i++)
                        u[i] = s[i] ^ e[i];
                    e = f.slice(0, 16),
                        c = c.concat(u),
                        o++
                }
            var h = c;
            for (t.isPadding && t.mode == this.SM4_DECRYPT && (h = this.padding(h, this.SM4_DECRYPT)),
                     i = 0; i < h.length; i++)
                h[i] < 0 && (h[i] = h[i] + 256);
            return h
        }
}

function SM4Params() {
    this.mode = 1, this.isPadding = !0, this.sk = new Array(32)
}

stringToByte1 = function (t) {
    var e, r, n = new Array;
    e = t.length;
    for (var i = 0; i < e; i++)
        (r = t.charCodeAt(i)) >= 65536 && r <= 1114111 ? (n.push(r >> 18 & 7 | 240),
            n.push(r >> 12 & 63 | 128),
            n.push(r >> 6 & 63 | 128),
            n.push(63 & r | 128)) : r >= 2048 && r <= 65535 ? (n.push(r >> 12 & 15 | 224),
            n.push(r >> 6 & 63 | 128),
            n.push(63 & r | 128)) : r >= 128 && r <= 2047 ? (n.push(r >> 6 & 31 | 192),
            n.push(63 & r | 128)) : n.push(255 & r);
    for (var o = new Array, s = 0; s < n.length; s++) {
        var u = n[s];
        o[s] = u - 256
    }
    return o
}

stringToByte = function (t) {
    var e, r, n = new Array;
    e = t.length;
    for (var i = 0; i < e; i++)
        (r = t.charCodeAt(i)) >= 65536 && r <= 1114111 ? (n.push(r >> 18 & 7 | 240),
            n.push(r >> 12 & 63 | 128),
            n.push(r >> 6 & 63 | 128),
            n.push(63 & r | 128)) : r >= 2048 && r <= 65535 ? (n.push(r >> 12 & 15 | 224),
            n.push(r >> 6 & 63 | 128),
            n.push(63 & r | 128)) : r >= 128 && r <= 2047 ? (n.push(r >> 6 & 31 | 192),
            n.push(63 & r | 128)) : n.push(255 & r);
    return n
}

hexStringToBytes = function (t) {
    if (null == t || "" === t)
        return null;
    for (var e = (t = t.toUpperCase()).length / 2 | 0, r = t.split(""), n = new Array, i = 0; i < e; i++) {
        var o = 2 * i;
        n[i] = intToByte(charToByte(r[o]) << 4 | charToByte(r[o + 1]) | 0)
    }
    return n
}

intToByte = function (t) {
    var e = 255 & t;
    return e >= 128 ? -1 * (128 - e % 128) : e
}

charToByte = function (t) {
    return 0 | "0123456789ABCDEF".indexOf(t)
}

byteToHex = function (t) {
    for (var e = "", r = "", n = 0; n < t.length; n++)
        1 === (r = (255 & t[n]).toString(16)).length ? e = e + "0" + r : e += r;
    return e.toUpperCase()
}

fromUint8Array = function (t) {
    let e = []; // 初始化一个空数组用于存储每一块处理后的字符串
    for (let r = 0; r < t.length; r += 4096) { // 遍历Uint8Array，每次处理4096个字节
        let chunk = t.subarray(r, r + 4096); // 获取当前处理的字节块
        let chars = Array.from(chunk).map(byte => String.fromCharCode(byte)); // 将字节块内的每个字节转换为字符
        e.push(chars.join('')); // 将字符数组连接成字符串并添加到结果数组中
    }
    return btoa(e.join('')); // 将所有字符串块合并后进行Base64编码
}

sm4encrypt = function (encryptData, secretKey = 'A4769F49630C4414A80C4FD7DC4B8EB3', iv = '30303030303030304040404040404040') {
    let e = new SM4Util, r = new SM4Params;
    r.isPadding = !0, r.mode = e.SM4_ENCRYPT;
    let n = hexStringToBytes(secretKey), i = hexStringToBytes(iv);
    e.sm4_setkey_enc(r, n);
    let o = stringToByte1(encryptData)
        , c = e.sm4_crypt_cbc(r, i, o)
        , f = byteToHex(c)
        , h = stringToByte(f)
        , p = fromUint8Array(new Uint8Array(h));
    return null != p && p.trim().length > 0 && p.replace(/(\s*|\t|\r|\n)/g, ""), p
}
