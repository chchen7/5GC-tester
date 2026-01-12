db = db.getSiblingDB("free5gc");

var cols = [
    "subscriptionData.authenticationData.authenticationSubscription",
    "subscriptionData.provisionedData.amData",
    "subscriptionData.provisionedData.smData",
    "subscriptionData.provisionedData.smfSelectionSubscriptionData",
    "subscriptionData.identityData",
    "policyData.ues.amData",
    "policyData.ues.smData"
];

cols.forEach(function(c) { db.getCollection(c).deleteMany({}); });

var num_ues = 100; 
var plmn = "20893";

for (var i = 1; i <= num_ues; i++) {
    var imsiSuffix = i.toString().padStart(10, '0');
    var ueId = "imsi-" + plmn + imsiSuffix;
    
    db.getCollection("subscriptionData.authenticationData.authenticationSubscription").insert({
        "ueId": ueId,
        "authenticationMethod": "5G_AKA",
        "authenticationManagementField": "8000",
        "sequenceNumber": { 
            "sqnScheme": "GENERAL", 
            "sqn": "000000000023" 
        },
        "encPermanentKey": "8baf473f2f8fd09487cccbd7097c6862",
        "encOpcKey": "8e27b6af0e692e750f32667a3b14605d"
    });

    db.getCollection("subscriptionData.identityData").insert({
        "ueId": ueId,
        "gpsi": "msisdn-"
    });

    db.getCollection("subscriptionData.provisionedData.amData").insert({
        "ueId": ueId,
        "servingPlmnId": plmn,
        "gpsis": [ "msisdn-" ],
        "subscribedUeAmbr": { "uplink": "1 Gbps", "downlink": "2 Gbps" },
        "nssai": {
            "defaultSingleNssais": [ { "sst": 1, "sd": "010203" } ],
            "singleNssais": [ { "sst": 1, "sd": "112233" } ]
        }
    });

    // 4. SM Data (Session Management)
    var dnnConfigs = {
        "internet": {
            "pduSessionTypes": { "defaultSessionType": "IPV4", "allowedSessionTypes": [ "IPV4" ] },
            "sscModes": { "defaultSscMode": "SSC_MODE_1", "allowedSscModes": [ "SSC_MODE_2", "SSC_MODE_3" ] },
            "5gQosProfile": { "5qi": 9, "arp": { "priorityLevel": 8, "preemptCap": "", "preemptVuln": "" }, "priorityLevel": 8 },
            "sessionAmbr": { "uplink": "1000 Mbps", "downlink": "1000 Mbps" }
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


    db.getCollection("subscriptionData.provisionedData.smfSelectionSubscriptionData").insert({
        "ueId": ueId,
        "servingPlmnId": plmn,
        "subscribedSnssaiInfos": {
            "01010203": { "dnnInfos": [ { "dnn": "internet" } ] },
            "01112233": { "dnnInfos": [ { "dnn": "internet" } ] }
        }
    });

    db.getCollection("policyData.ues.amData").insert({
        "ueId": ueId, "subscCats": [ "free5gc" ]
    });

    db.getCollection("policyData.ues.smData").insert({
        "ueId": ueId,
        "smPolicySnssaiData": {
            "01010203": {
                "snssai": { "sst": 1, "sd": "010203" },
                "smPolicyDnnData": { "internet": { "dnn": "internet" } }
            },
            "01112233": {
                "snssai": { "sst": 1, "sd": "112233" },
                "smPolicyDnnData": { "internet": { "dnn": "internet" } }
            }
        }
    });
}
print("Successfully populated " + num_ues + " UEs into free5gc.");
