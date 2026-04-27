package ue

import (
	"bytes"
	"encoding/hex"
	"fmt"
	"regexp"

	"github.com/free5gc/nas"
	"github.com/free5gc/nas/nasMessage"
	"github.com/free5gc/nas/security"
	"github.com/free5gc/util/milenage"
	"github.com/free5gc/util/ueauth"
)

func milenageF1(opc, k, rand, sqn, amf []byte, macA, macS []byte) error {
	ik, ck, xres, autn, err := milenage.GenerateAKAParameters(opc, k, rand, sqn, amf)
	if err != nil {
		return err
	}
	// Suppress unused variable warnings
	_ = ik
	_ = ck
	_ = xres

	// AUTN = (SQN xor AK) || AMF || MAC-A
	// MAC-A is the last 8 bytes of AUTN
	if len(autn) >= 8 && macA != nil {
		copy(macA, autn[len(autn)-8:])
	}

	// For MAC-S, use resync AMF (0000)
	if macS != nil {
		resyncAMFBytes, err := hex.DecodeString("0000")
		if err != nil {
			return err
		}
		ikS, ckS, xresS, autnS, err := milenage.GenerateAKAParameters(opc, k, rand, sqn, resyncAMFBytes)
		if err != nil {
			return err
		}
		// Suppress unused variable warnings
		_ = ikS
		_ = ckS
		_ = xresS

		if len(autnS) >= 8 {
			copy(macS, autnS[len(autnS)-8:])
		}
	}

	return nil
}

func milenageF2345(opc, k, rand []byte, res, ck, ik, ak, akstar []byte) error {
	// Use GenerateAKAParameters to get basic parameters
	ikOut, ckOut, resOut, autn, err := milenage.GenerateAKAParameters(opc, k, rand, make([]byte, 6), make([]byte, 2))
	if err != nil {
		return err
	}

	// Use GenerateKeysWithAUTN to get AK
	sqnhe, akOut, ikOut2, ckOut2, resOut2, err := milenage.GenerateKeysWithAUTN(opc, k, rand, autn)
	if err != nil {
		return err
	}
	// Suppress unused variable warnings
	_ = sqnhe
	_ = ikOut2
	_ = ckOut2
	_ = resOut2

	// Copy results to output parameters
	if res != nil {
		copy(res, resOut)
	}
	if ck != nil {
		copy(ck, ckOut)
	}
	if ik != nil {
		copy(ik, ikOut)
	}
	if ak != nil {
		copy(ak, akOut)
	}
	if akstar != nil {
		// For AK*, we need to use a different SQN, but due to API limitations, we use the same value for now
		copy(akstar, akOut)
	}

	return nil
}

func deriveKAmf(supi string, key []byte, snName string, SQN, AK []byte) ([]byte, error) {
	FC := ueauth.FC_FOR_KAUSF_DERIVATION
	P0 := []byte(snName)
	SQNxorAK := make([]byte, 6)
	for i := 0; i < len(SQN); i++ {
		SQNxorAK[i] = SQN[i] ^ AK[i]
	}
	P1 := SQNxorAK
	Kausf, err := ueauth.GetKDFValue(key, FC, P0, ueauth.KDFLen(P0), P1, ueauth.KDFLen(P1))
	if err != nil {
		return nil, fmt.Errorf("GetKDFValue error: %+v", err)
	}
	P0 = []byte(snName)
	Kseaf, err := ueauth.GetKDFValue(Kausf, ueauth.FC_FOR_KSEAF_DERIVATION, P0, ueauth.KDFLen(P0))
	if err != nil {
		return nil, fmt.Errorf("GetKDFValue error: %+v", err)
	}

	supiRegexp, err := regexp.Compile("(?:imsi|supi)-([0-9]{5,15})")
	if err != nil {
		return nil, fmt.Errorf("regexp Compile error: %+v", err)
	}
	groups := supiRegexp.FindStringSubmatch(supi)

	P0 = []byte(groups[1])
	L0 := ueauth.KDFLen(P0)
	P1 = []byte{0x00, 0x00}
	L1 := ueauth.KDFLen(P1)

	return ueauth.GetKDFValue(Kseaf, ueauth.FC_FOR_KAMF_DERIVATION, P0, L0, P1, L1)
}

func deriveAlgorithmKey(kAmf []byte, cipheringAlgorithm, integrityAlgorithm uint8) ([]byte, []byte, error) {
	// Security Key
	P0 := []byte{security.NNASEncAlg}
	L0 := ueauth.KDFLen(P0)
	P1 := []byte{cipheringAlgorithm}
	L1 := ueauth.KDFLen(P1)

	kenc, err := ueauth.GetKDFValue(kAmf, ueauth.FC_FOR_ALGORITHM_KEY_DERIVATION, P0, L0, P1, L1)
	if err != nil {
		return nil, nil, fmt.Errorf("GetKDFValue error: %+v", err)
	}

	// Integrity Key
	P0 = []byte{security.NNASIntAlg}
	L0 = ueauth.KDFLen(P0)
	P1 = []byte{integrityAlgorithm}
	L1 = ueauth.KDFLen(P1)

	kint, err := ueauth.GetKDFValue(kAmf, ueauth.FC_FOR_ALGORITHM_KEY_DERIVATION, P0, L0, P1, L1)
	if err != nil {
		return nil, nil, fmt.Errorf("GetKDFValue error: %+v", err)
	}

	return kenc, kint, nil
}

func deriveSequenceNumber(autn []byte, ak []uint8) []byte {
	sqn := make([]byte, 6)

	sqnXorAk := autn[0:6]

	for i := 0; i < len(sqnXorAk); i++ {
		sqn[i] = sqnXorAk[i] ^ ak[i]
	}

	return sqn
}

func deriveResStarAndSetKey(supi string, cipheringAlgorithm, integrityAlgorithm uint8, sqn, amf, encPermanentKey, encOpcKey string, rand []byte, autn []byte, snName string) ([]byte, []byte, []byte, []byte, string, error) {
	sqnHex, err := hex.DecodeString(sqn)
	if err != nil {
		return nil, nil, nil, nil, "", fmt.Errorf("error decode sqn: %v", err)
	}

	amfHex, err := hex.DecodeString(amf)
	if err != nil {
		return nil, nil, nil, nil, "", fmt.Errorf("error decode amf: %v", err)
	}

	kHex, err := hex.DecodeString(encPermanentKey)
	if err != nil {
		return nil, nil, nil, nil, "", fmt.Errorf("error decode encPermanentKey: %v", err)
	}

	opcHex, err := hex.DecodeString(encOpcKey)
	if err != nil {
		return nil, nil, nil, nil, "", fmt.Errorf("error decode encOpcKey: %v", err)
	}

	macA, macS := make([]byte, 8), make([]byte, 8)
	ck, ik := make([]byte, 16), make([]byte, 16)
	res := make([]byte, 8)
	ak, akStar := make([]byte, 6), make([]byte, 6)

	// generate macA and macS
	if err := milenageF1(opcHex, kHex, rand, sqnHex, amfHex, macA, macS); err != nil {
		return nil, nil, nil, nil, "", fmt.Errorf("error F1: %v", err)
	}

	//generate res, ck, ik, ak, akstar
	if err := milenageF2345(opcHex, kHex, rand, res, ck, ik, ak, akStar); err != nil {
		return nil, nil, nil, nil, "", fmt.Errorf("error F2345: %v", err)
	}

	// update sqn if sqn is not equal to autn's sqn
	if newSqn := deriveSequenceNumber(autn[:], ak[:]); !bytes.Equal(sqnHex, newSqn) {
		sqnHex = newSqn
	}

	// derive RES*
	key := append(ck, ik...)
	FC := ueauth.FC_FOR_RES_STAR_XRES_STAR_DERIVATION
	P0 := []byte(snName)
	P1 := rand
	P2 := res

	kAmf, err := deriveKAmf(supi, key, snName, sqnHex, ak)
	if err != nil {
		return nil, nil, nil, nil, "", fmt.Errorf("error deriveKAmf: %v", err)
	}
	kenc, kint, err := deriveAlgorithmKey(kAmf, cipheringAlgorithm, integrityAlgorithm)
	if err != nil {
		return nil, nil, nil, nil, "", fmt.Errorf("error deriveAlgorithmKey: %v", err)
	}
	kdfVal_for_resStar, err := ueauth.GetKDFValue(key, FC, P0, ueauth.KDFLen(P0), P1, ueauth.KDFLen(P1), P2, ueauth.KDFLen(P2))
	if err != nil {
		return nil, nil, nil, nil, "", fmt.Errorf("error GetKDFValue: %v", err)
	}
	return kAmf, kenc, kint, kdfVal_for_resStar[len(kdfVal_for_resStar)/2:], hex.EncodeToString(sqnHex), nil
}

func encodeNasPduWithSecurity(nasPdu []byte, securityHeaderType uint8, ue *Ue, securityContextAvailable bool, newSecurityContext bool) ([]byte, error) {
	m := nas.NewMessage()
	if err := m.PlainNasDecode(&nasPdu); err != nil {
		return nil, err
	}

	m.SecurityHeader = nas.SecurityHeader{
		ProtocolDiscriminator: nasMessage.Epd5GSMobilityManagementMessage,
		SecurityHeaderType:    securityHeaderType,
	}

	return nasEncode(m, securityContextAvailable, newSecurityContext, ue)
}
