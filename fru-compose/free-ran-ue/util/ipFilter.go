package util

import (
	"net"
)

func IsIpInSpecifiedFlow(rawPacket []byte, specifiedFlow []string) bool {
	if len(rawPacket) < 20 {
		return false
	}

	version := rawPacket[0] >> 4
	if version != 4 {
		return false
	}

	headerLength := int(rawPacket[0]&0x0F) * 4
	if len(rawPacket) < headerLength || headerLength < 20 {
		return false
	}

	destIP := net.IPv4(rawPacket[16], rawPacket[17], rawPacket[18], rawPacket[19])
	for _, cidr := range specifiedFlow {
		if cidr == "" {
			continue
		}

		_, network, err := net.ParseCIDR(cidr)
		if err != nil {
			panic(err)
		}

		if network.Contains(destIP) {
			return true
		}
	}

	return false
}
