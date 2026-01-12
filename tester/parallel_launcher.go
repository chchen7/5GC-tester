package main

import (
	"flag"
	"fmt"
	"os/exec"
	"sync"
)

func main() {
	n := flag.Int("n", 1, "(ueransim-gnb-1 ~ ueransim-gnb-n)")
	ueCount := flag.Int("u", 100, "number of ue")
	tempo := flag.Int("t", 1000, "Interval (ms) between launching each UE")
	flag.Parse()

	var wg sync.WaitGroup
	gate := make(chan struct{})

	for i := 1; i <= *n; i++ {
		wg.Add(1)
		containerName := fmt.Sprintf("ueransim-ueransim-gnb-%d", i)
		yamlPath := fmt.Sprintf("./config/uecfg.yaml")
		startimsi := 208930000000001+(i-1)*(*ueCount)
		go func(name string, path string) {
			defer wg.Done()
			cmd := exec.Command("docker", "exec", "-d", name, "./launch_ue.sh", "-n", fmt.Sprintf("%d",*ueCount),"-t", fmt.Sprintf("%d", *tempo), "-i", fmt.Sprintf("%d",startimsi))
			<-gate 

			output, err := cmd.CombinedOutput()
			if err != nil {
				fmt.Printf("[%s] fail: %v\n", name, err)
			} else {
				fmt.Printf("[%s] sucess\n", name)
				_ = output
			}
		}(containerName, yamlPath)
	}

	fmt.Println("start...")
	close(gate) 

	wg.Wait()
	fmt.Println("finish")
}