#!/usr/bin/env python3
"""
Hand Gesture Interaction System with EKF
Main Application Entry Point
"""
import argparse
from core.orchestrator import HandTrackingOrchestrator


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Hand Gesture Interaction System with EKF',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Demo mode
  python main.py --mode mouse       # Virtual mouse
  python main.py --mode volume      # Volume control
  python main.py --mode draw        # Air drawing
  python main.py --no-ekf           # Disable EKF smoothing
  python main.py --camera 1         # Use camera 1
        """
    )
    
    parser.add_argument(
        "--mode",
        choices=["demo", "mouse", "volume", "draw"],
        default="demo",
        help="Operating mode",
    )
    
    parser.add_argument('--camera', 
                       type=int, 
                       default=0,
                       help='Camera device ID')
    
    parser.add_argument('--no-ekf', 
                       action='store_true',
                       help='Disable Extended Kalman Filter')
    
    args = parser.parse_args()
    
    # Print banner
    print("\n" + "="*60)
    print("HAND GESTURE INTERACTION SYSTEM (EKF)")
    print("  Advanced Vision-Based Interaction Project")
    print("="*60 + "\n")
    
    app = HandTrackingOrchestrator(mode=args.mode, use_ekf=not args.no_ekf)
    app.run(camera_id=args.camera)


if __name__ == "__main__":
    main()
