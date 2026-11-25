# Mechanical assembly

Choose a four-wheel chassis and head brackets that fit your selected motors,
display and board mounts. This is a functional assembly guide; no dimensioned CAD,
STL or universal hole pattern is supplied. Record dimensions and photographs in your
private build worksheet before drilling or ordering brackets.

## Base and wheels

1. Disconnect both power supplies and support the chassis securely.
2. Attach four matched geared DC motors using their correct brackets and fasteners.
   A/B channels on the left driver control the two left motors; the right driver
   controls the right pair. Fit wheels squarely without rubbing a bracket.
3. Confirm wheel diameter, total mass, floor grip and motor torque are suitable.
   The two motors on each side receive the same speed command; no encoders are read.
4. Put heavy supplies low and near the centre, with protected connectors and an
   accessible actuator-power cutoff. Do not obstruct cell ventilation.
5. Mount Pi, Mega and motor drivers on insulated standoffs. Leave USB, HDMI, storage,
   cooling and inspection access. Do not route motor current through Pi connectors.

## Display and head

1. Mount the landscape HDMI/USB-touch display so its weight is supported by brackets,
   not connectors. Secure the USB and HDMI leads with strain relief.
2. Fit the pan and tilt geared unipolar steppers with their matching ULN2003 boards.
   Use the motor's rated supply; the reference actuator rail is 5 V.
3. Balance the head so loss of coil power cannot make it fall. The firmware releases
   coils after stopping; a motor/gearbox that needs powered holding torque requires
   a different mechanical design.
4. Establish visible centre marks while motor power is off. Move the bracket only
   using its designed adjustment; do not force a geared shaft by hand.
5. Leave cable loops long enough for small commissioning jogs and clamp them clear
   of pinch points. Treat shipped step limits as software bounds, not tested geometry.

## Place the sensors

| Sensor | Position and acceptance concern |
|---|---|
| ToF 0 | Front-left; unobstructed view ahead, fixed to the base |
| ToF 1 | Front-right; complementary view, no body panel in its optical path |
| ToF 2 | Rear; rear readings must be valid even though reverse is off |
| Cliff 0 | Front-left, downward-facing, close enough to detect every intended floor |
| Cliff 1 | Rear-centre, downward-facing |
| Cliff 2 | Front-right, downward-facing |
| MPU6050 | Rigidly attached to the base, not the moving head; mark its up direction |
| PIR | Clear view; allow its documented stabilization time |
| Head/back touch | Insulate signal pads from metalwork; use momentary active-high modules |
| Camera and LED | Pi-compatible camera with a nearby visible activity indicator |

TCRT5000 module height depends on surface and trimmer setting. Test dark/light flooring,
transitions and ambient light at the final mounting height. Place the front sensors
far enough ahead of the wheels that measured stopping distance fits inside the margin.
Do not test on a real staircase. Use a secured chassis and a removable floor target.

## Audio and final inspection

Mount the two INMP441 microphones and amplified speakers with physical separation and
strain relief. Keep motor leads away from audio/sensor leads. The supported voice
path takes turns. Simultaneous listening requires the optional local echo-cancel setup at M13.

Check all fasteners, insulation, wheel clearance, head retention, sensor visibility,
airflow and cutoff reach. Make the first wiring checks with all supplies unplugged.
Continue with [Wire every part](WIRING.md), then [Software setup](SETUP_GUIDE.md).
