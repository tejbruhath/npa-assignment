# tcp_reno_simulator.py
import matplotlib.pyplot as plt
import random

class TCPRenoSimulator:
    def __init__(self, rtt=1, loss_rate=0.01, duration=50):
        self.rtt = rtt
        self.loss_rate = loss_rate
        self.duration = duration
        
        self.cwnd = 1.0
        self.ssthresh = float('inf')
        self.state = "SLOW_START"
        self.dup_acks = 0
        self.packets_sent = 0
        self.acked_packets = 0
        self.time = 0
        
        self.cwnd_history = []
        self.time_history = []

    def send_packet(self):
        self.packets_sent += 1
        # Simulate loss
        if random.random() < self.loss_rate:
            return False  # Lost
        return True   # ACKed

    def run(self):
        while self.time < self.duration:
            # Send up to cwnd packets per RTT
            packets_in_flight = 0
            acks_received = 0
            losses = 0

            for _ in range(int(self.cwnd)):
                if self.send_packet():
                    acks_received += 1
                else:
                    losses += 1
                packets_in_flight += 1

            # Update state
            if losses > 0:
                # Triple duplicate ACK or timeout
                if acks_received >= 3:
                    # Fast retransmit & recovery
                    self.ssthresh = self.cwnd / 2
                    self.cwnd = self.ssthresh + 3
                    self.state = "FAST_RECOVERY"
                    print(f"[t={self.time}] Triple Dup ACK → Fast Recovery, cwnd={self.cwnd:.2f}")
                else:
                    # Timeout
                    self.ssthresh = self.cwnd / 2
                    self.cwnd = 1.0
                    self.state = "SLOW_START"
                    print(f"[t={self.time}] Timeout → Slow Start, cwnd=1.0")
            else:
                if self.state == "SLOW_START":
                    self.cwnd += acks_received
                    if self.cwnd >= self.ssthresh:
                        self.state = "CONGESTION_AVOIDANCE"
                elif self.state == "CONGESTION_AVOIDANCE":
                    self.cwnd += acks_received / self.cwnd
                elif self.state == "FAST_RECOVERY":
                    self.cwnd += acks_received
                    if self.cwnd >= self.ssthresh:
                        self.cwnd = self.ssthresh
                        self.state = "CONGESTION_AVOIDANCE"

            # Record
            self.time += self.rtt
            self.cwnd_history.append(self.cwnd)
            self.time_history.append(self.time)

            print(f"[t={self.time:.1f}] cwnd={self.cwnd:.2f}, state={self.state}")

        self.plot()

    def plot(self):
        plt.figure(figsize=(10, 6))
        plt.plot(self.time_history, self.cwnd_history, 'b-o', label='cwnd', markersize=4)
        plt.title('TCP Reno Congestion Window Evolution')
        plt.xlabel('Time (RTTs)')
        plt.ylabel('Congestion Window (packets)')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.show()

# === RUN SIMULATION ===
if __name__ == "__main__":
    print("Starting TCP Reno Congestion Control Simulation...\n")
    sim = TCPRenoSimulator(rtt=1, loss_rate=0.02, duration=30)
    sim.run()