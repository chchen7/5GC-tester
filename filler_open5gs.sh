#!/bin/bash
N=1
while getopts "n:" opt; do
  case $opt in
    n) N=$OPTARG ;;
    *) echo "Usage: $0 -n [Multiplier]" >&2; exit 1 ;;
  esac
done

TOTAL_COUNT=$((N * 100))
echo "[INFO] Injecting $TOTAL_COUNT subscribers into 'open5gs' DB with STRICT TYPES..."

docker exec -i mongo mongosh open5gs --quiet <<EOF

db.subscribers.drop();
db.subscribers.createIndex({ "imsi": 1 }, { unique: true });

var i = 1;
while (i <= $TOTAL_COUNT) {
    var suffix = ("0000000000" + i).slice(-10);
    var targetImsi = "20893" + suffix;
    db.subscribers.insertOne({
        "imsi": targetImsi,
        "subscribed_rau_tau_timer": NumberInt(12),
        "network_access_mode": NumberInt(2),
        "subscriber_status": NumberInt(0),
        "access_restriction_data": NumberInt(32),
        "slice": [{
            "sst": NumberInt(1),
            "default_indicator": true,
            "sd": "000001",
            "_id": ObjectId(),           
            "session": [{
                "name": "default",
                "type": NumberInt(3),
                "_id": ObjectId(),      
                "pcc_rule": [],
                "ambr": { 
                    "uplink": { "value": NumberInt(1), "unit": NumberInt(3) }, 
                    "downlink": { "value": NumberInt(1), "unit": NumberInt(3) } 
                },
                "qos": { 
                    "index": NumberInt(9), 
                    "arp": { 
                        "priority_level": NumberInt(8), 
                        "pre_emption_capability": NumberInt(1), 
                        "pre_emption_vulnerability": NumberInt(1) 
                    } 
                }
            }]
        }],
        "ambr": {
            "uplink": { "value": NumberInt(1), "unit": NumberInt(3) },
            "downlink": { "value": NumberInt(1), "unit": NumberInt(3) }
        },
        "security": {
            "k": "465B5CE8B199B49FAA5F0A2EE238A6BC",
            "amf": "8000",
            "op": null,
            "opc": "E8ED289DEBA952E4283B54E88E6183CA",
            "sqn": NumberLong("200000")  
        },
        "msisdn": [],
        "schema_version": NumberInt(1),
        "__v": NumberInt(0)
    });
    i++;
}
print("[SUCCESS] Successfully injected " + (i-1) + " subscribers into open5gs.");
EOF