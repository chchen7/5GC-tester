db = db.getSiblingDB("free5gc");

var cols = [
    "subscriptionData.authenticationData.authenticationSubscription",
    "subscriptionData.provisionedData.amData",
    "subscriptionData.provisionedData.smData",
    "policyData.ues.amData",
    "policyData.ues.smData"
];

// 清空舊資料
cols.forEach(function(c) { db.getCollection(c).deleteMany({}); });

var num_ues = 100; 
var plmn = "20893"; 

for (var i = 1; i <= num_ues; i++) {
    var imsiSuffix = i.toString().padStart(10, '0');
    var ueId = "imsi-" + plmn + imsiSuffix;
    
    // 1. Authentication Data
    db.getCollection("subscriptionData.authenticationData.authenticationSubscription").insert({
        "ueId": ueId,
        "authenticationMethod": "5G_AKA",
        "authenticationManagementField": "8000",
        "sequenceNumber": "000000000023", 
        "permanentKey": {
            "permanentKeyValue": "8baf473f2f8fd09487cccbd7097c6862",
            "encryptionKey": 0,
            "encryptionAlgorithm": 0
        },
        "opc": {
            "opcValue": "8e27b6af0e692e750f32667a3b14605d",
            "encryptionKey": 0,
            "encryptionAlgorithm": 0
        },
        "milenage": {
            "op": { "opValue": "", "encryptionKey": 0, "encryptionAlgorithm": 0 }
        }
    });

    // 2. AM Data
    db.getCollection("subscriptionData.provisionedData.amData").insert({
        "ueId": ueId,
        "servingPlmnId": plmn,
        "gpsis": [ "msisdn-0900000000" ],
        "subscribedUeAmbr": { "uplink": "1 Gbps", "downlink": "2 Gbps" },
        "nssai": {
            "defaultSingleNssais": [ 
                { "sst": 1, "sd": "010203" }, 
                { "sst": 1, "sd": "112233" } 
            ]
        }
    });

    // 3. SM Data
    var dnnConfigs = {
        "internet": {
            "pduSessionTypes": { "defaultSessionType": "IPV4", "allowedSessionTypes": [ "IPV4" ] },
            "sscModes": { "defaultSscMode": "SSC_MODE_1", "allowedSscModes": [ "SSC_MODE_2", "SSC_MODE_3" ] },
            "5gQosProfile": { "5qi": 9, "arp": { "priorityLevel": 8, "preemptCap": "", "preemptVuln": "" }, "priorityLevel": 8 },
            "sessionAmbr": { "uplink": "200 Mbps", "downlink": "100 Mbps" }
        },
        "internet2": {
            "pduSessionTypes": { "defaultSessionType": "IPV4", "allowedSessionTypes": [ "IPV4" ] },
            "sscModes": { "defaultSscMode": "SSC_MODE_1", "allowedSscModes": [ "SSC_MODE_2", "SSC_MODE_3" ] },
            "5gQosProfile": { "5qi": 9, "arp": { "priorityLevel": 8, "preemptCap": "", "preemptVuln": "" }, "priorityLevel": 8 },
            "sessionAmbr": { "uplink": "200 Mbps", "downlink": "100 Mbps" }
        }
    };

    db.getCollection("subscriptionData.provisionedData.smData").insert({
        "ueId": ueId, "servingPlmnId": plmn, "singleNssai": { "sst": 1, "sd": "010203" },
        "dnnConfigurations": dnnConfigs
    });
    db.getCollection("subscriptionData.provisionedData.smData").insert({
        "ueId": ueId, "servingPlmnId": plmn, "singleNssai": { "sst": 1, "sd": "112233" },
        "dnnConfigurations": dnnConfigs
    });

    // 4. Policy AM Data
    db.getCollection("policyData.ues.amData").insert({
        "ueId": ueId, "subscCats": [ "free5gc" ]
    });

    // 5. Policy SM Data
    db.getCollection("policyData.ues.smData").insert({
        "ueId": ueId,
        "smPolicySnssaiData": {
            "01010203": {
                "snssai": { "sst": 1, "sd": "010203" },
                "smPolicyDnnData": { "internet": { "dnn": "internet" }, "internet2": { "dnn": "internet2" } }
            },
            "01112233": {
                "snssai": { "sst": 1, "sd": "112233" },
                "smPolicyDnnData": { "internet": { "dnn": "internet" }, "internet2": { "dnn": "internet2" } }
            }
        }
    });
}
print("Successfully populated " + num_ues + " UEs.");
