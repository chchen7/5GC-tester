package gnb

import (
	"net"

	"github.com/free5gc/aper"
)

type XnUe struct {
	imsi string

	ulTeid aper.OctetString
	dlTeid aper.OctetString

	dataPlaneAddress *net.UDPAddr
}

func NewXnUe(imsi string, dlTeid aper.OctetString, dataPlaneAddress *net.UDPAddr) *XnUe {
	return &XnUe{
		imsi: imsi,

		ulTeid: aper.OctetString{},
		dlTeid: dlTeid,

		dataPlaneAddress: dataPlaneAddress,
	}
}

func (x *XnUe) Release(teidGenerator *TeidGenerator) {
	teidGenerator.ReleaseTeid(x.dlTeid)
}

func (x *XnUe) GetIMSI() string {
	return x.imsi
}

func (x *XnUe) GetUlTeid() aper.OctetString {
	return x.ulTeid
}

func (x *XnUe) GetDlTeid() aper.OctetString {
	return x.dlTeid
}

func (x *XnUe) GetDataPlaneAddress() *net.UDPAddr {
	return x.dataPlaneAddress
}

func (x *XnUe) SetUlTeid(ulTeid aper.OctetString) {
	x.ulTeid = ulTeid
}

func (x *XnUe) SetDataPlaneAddress(dataPlaneAddress *net.UDPAddr) {
	x.dataPlaneAddress = dataPlaneAddress
}
