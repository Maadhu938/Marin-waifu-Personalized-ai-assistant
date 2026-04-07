/* Avatar canvas drawing logic ported from the prototype */

export class MarinCanvasEngine {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    
    this.state = {
      isSpeaking: false,
      emotion: 'happy', // happy, curious, sad, teasing, excited
      mousePos: { x: 0, y: 0 },
      breathing: 0,
      blinkTimer: 0,
      isBlinking: false
    };

    this.colors = {
      hairLine: '#1a1a2e',
      hairLight: '#ffe6f2',
      hairMid: '#ffb3d9',
      hairDark: '#ff66b3',
      skinLight: '#fff0f5',
      skinShadow: '#ffe0eb',
      eyeWhite: '#ffffff',
      eyeIris: '#00e5ff',
      eyeIrisDark: '#008b99',
      clothesMain: '#2a2a35',
      clothesShadow: '#1a1a25',
      clothesAccent: '#404050'
    };

    this.animationFrameId = null;
    this.startTime = Date.now();
  }

  start() {
    if (this.animationFrameId) return;
    const render = () => {
      this.draw();
      this.animationFrameId = requestAnimationFrame(render);
    };
    render();
  }

  stop() {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
  }

  setState(newState) {
    this.state = { ...this.state, ...newState };
  }

  draw() {
    const { width, height } = this.canvas;
    const ctx = this.ctx;
    
    ctx.clearRect(0, 0, width, height);
    
    // Constants based on canvas size
    const centerX = width / 2;
    const centerY = height * 0.45;  // Slightly above center
    const scale = Math.min(width, height) / 400; // Base scale on 400px reference
    
    // Time-based animations
    const time = (Date.now() - this.startTime) / 1000;
    this.state.breathing = Math.sin(time * 2) * 5 * scale;
    
    // Blinking logic
    this.state.blinkTimer--;
    if (this.state.blinkTimer <= 0) {
      this.state.isBlinking = true;
      if (this.state.blinkTimer < -5) {
        this.state.isBlinking = false;
        this.state.blinkTimer = Math.random() * 200 + 100;
      }
    }
    
    // Speaking logic (mouth movement)
    const mouthOpen = this.state.isSpeaking ? Math.abs(Math.sin(time * 15)) * 10 * scale : 2 * scale;
    
    // Eye tracking math
    const lookX = (this.state.mousePos.x - width / 2) * 0.05 * scale;
    const lookY = (this.state.mousePos.y - height / 2) * 0.05 * scale;
    
    ctx.save();
    // Bounce effect for excitement
    if (this.state.emotion === 'excited') {
      ctx.translate(0, this.state.breathing + Math.abs(Math.sin(time * 8)) * 10 * scale);
    } else {
      ctx.translate(0, this.state.breathing);
    }
    
    this.drawBody(ctx, centerX, centerY, scale);
    this.drawHead(ctx, centerX, centerY, scale, lookX, lookY);
    this.drawHair(ctx, centerX, centerY, scale, time);
    this.drawFace(ctx, centerX, centerY, scale, lookX, lookY, mouthOpen);
    
    ctx.restore();
    
    this.drawParticles(ctx, width, height, time, scale);
  }

  drawBody(ctx, cx, cy, scale) {
    ctx.fillStyle = this.colors.clothesMain;
    ctx.beginPath();
    // Shoulders
    ctx.moveTo(cx - 100 * scale, cy + 180 * scale);
    ctx.quadraticCurveTo(cx, cy + 90 * scale, cx + 100 * scale, cy + 180 * scale);
    ctx.lineTo(cx + 120 * scale, cy + 300 * scale);
    ctx.lineTo(cx - 120 * scale, cy + 300 * scale);
    ctx.fill();
    ctx.lineWidth = 3 * scale;
    ctx.strokeStyle = this.colors.hairLine;
    ctx.stroke();

    // Collar
    ctx.fillStyle = this.colors.skinShadow;
    ctx.beginPath();
    ctx.moveTo(cx - 30 * scale, cy + 80 * scale);
    ctx.quadraticCurveTo(cx, cy + 110 * scale, cx + 30 * scale, cy + 80 * scale);
    ctx.fill();
    ctx.stroke();
  }

  drawHead(ctx, cx, cy, scale, lookX, lookY) {
    // Face base shape (moves slightly with look)
    cx += lookX * 0.5;
    cy += lookY * 0.5;
    
    ctx.fillStyle = this.colors.skinLight;
    ctx.beginPath();
    // Jaw and cheeks
    ctx.moveTo(cx - 70 * scale, cy - 20 * scale);
    ctx.quadraticCurveTo(cx - 70 * scale, cy + 60 * scale, cx - 40 * scale, cy + 85 * scale);
    ctx.quadraticCurveTo(cx, cy + 100 * scale, cx + 40 * scale, cy + 85 * scale);
    ctx.quadraticCurveTo(cx + 70 * scale, cy + 60 * scale, cx + 70 * scale, cy - 20 * scale);
    ctx.quadraticCurveTo(cx, cy - 70 * scale, cx - 70 * scale, cy - 20 * scale);
    ctx.fill();
    
    ctx.lineWidth = 2 * scale;
    ctx.strokeStyle = this.colors.hairLine;
    ctx.stroke();
  }

  drawHair(ctx, cx, cy, scale, time) {
    const hairMoveX = Math.sin(time) * 5 * scale;
    
    ctx.fillStyle = this.colors.hairMid;
    ctx.strokeStyle = this.colors.hairLine;
    ctx.lineWidth = 2 * scale;

    // Back hair
    ctx.beginPath();
    ctx.moveTo(cx - 70 * scale, cy);
    ctx.quadraticCurveTo(cx - 100 * scale - hairMoveX, cy + 150 * scale, cx - 60 * scale, cy + 180 * scale);
    ctx.quadraticCurveTo(cx - 90 * scale, cy + 120 * scale, cx - 60 * scale, cy + 60 * scale);
    ctx.fill();
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(cx + 70 * scale, cy);
    ctx.quadraticCurveTo(cx + 100 * scale - hairMoveX, cy + 150 * scale, cx + 60 * scale, cy + 180 * scale);
    ctx.quadraticCurveTo(cx + 90 * scale, cy + 120 * scale, cx + 60 * scale, cy + 60 * scale);
    ctx.fill();
    ctx.stroke();

    // Front bangs
    ctx.fillStyle = this.colors.hairLight;
    ctx.beginPath();
    ctx.moveTo(cx, cy - 80 * scale);
    ctx.quadraticCurveTo(cx - 80 * scale, cy - 70 * scale, cx - 90 * scale, cy + 20 * scale);
    ctx.quadraticCurveTo(cx - 60 * scale, cy - 30 * scale, cx - 40 * scale, cy - 30 * scale);
    ctx.quadraticCurveTo(cx - 20 * scale, cy - 10 * scale, cx, cy - 40 * scale);
    ctx.quadraticCurveTo(cx + 20 * scale, cy - 10 * scale, cx + 40 * scale, cy - 30 * scale);
    ctx.quadraticCurveTo(cx + 60 * scale, cy - 30 * scale, cx + 90 * scale, cy + 20 * scale);
    ctx.quadraticCurveTo(cx + 80 * scale, cy - 70 * scale, cx, cy - 80 * scale);
    ctx.fill();
    ctx.stroke();
    
    // Ahoge (antenna hair)
    ctx.beginPath();
    ctx.moveTo(cx, cy - 80 * scale);
    ctx.quadraticCurveTo(cx - 20 * scale - hairMoveX * 2, cy - 140 * scale, cx + 30 * scale, cy - 110 * scale);
    ctx.quadraticCurveTo(cx + 10 * scale, cy - 130 * scale, cx + 5 * scale, cy - 80 * scale);
    ctx.fill();
    ctx.stroke();
  }

  drawFace(ctx, cx, cy, scale, lookX, lookY, mouthOpen) {
    cx += lookX;
    cy += lookY;

    this.drawEyes(ctx, cx, cy, scale, lookX, lookY);
    this.drawBlush(ctx, cx, cy, scale);
    this.drawMouth(ctx, cx, cy, scale, mouthOpen);
    
    // Nose
    ctx.fillStyle = this.colors.hairLine;
    ctx.beginPath();
    ctx.arc(cx, cy + 35 * scale, 2 * scale, 0, Math.PI * 2);
    ctx.fill();
  }

  drawEyes(ctx, cx, cy, scale, lookX, lookY) {
    if (this.state.isBlinking) {
      // Drawn closed eyes
      ctx.strokeStyle = this.colors.hairLine;
      ctx.lineWidth = 3 * scale;
      ctx.beginPath();
      ctx.moveTo(cx - 50 * scale, cy + 5 * scale);
      ctx.quadraticCurveTo(cx - 35 * scale, cy + 15 * scale, cx - 20 * scale, cy + 5 * scale);
      ctx.stroke();
      
      ctx.beginPath();
      ctx.moveTo(cx + 50 * scale, cy + 5 * scale);
      ctx.quadraticCurveTo(cx + 35 * scale, cy + 15 * scale, cx + 20 * scale, cy + 5 * scale);
      ctx.stroke();
      return;
    }

    // Eye shape modifier based on emotion
    let eyeCurve = 35 * scale;
    let eyeHeight = 25 * scale;
    
    if (this.state.emotion === 'sad') {
      eyeCurve = 15 * scale; // drooping
    } else if (this.state.emotion === 'curious') {
      eyeHeight = 30 * scale; // wide
    } else if (this.state.emotion === 'teasing') {
      eyeHeight = 15 * scale; // narrowed
    }

    // Left Eye White
    ctx.fillStyle = this.colors.eyeWhite;
    ctx.beginPath();
    ctx.ellipse(cx - 35 * scale, cy, 15 * scale, eyeHeight, 0, 0, Math.PI * 2);
    ctx.fill();
    
    // Right Eye White
    ctx.beginPath();
    ctx.ellipse(cx + 35 * scale, cy, 15 * scale, eyeHeight, 0, 0, Math.PI * 2);
    ctx.fill();

    // Limit look inside eye wrapper
    const innerLookX = lookX * 0.4;
    const innerLookY = lookY * 0.4;

    // Left Iris
    ctx.fillStyle = this.colors.eyeIris;
    ctx.beginPath();
    ctx.ellipse(cx - 35 * scale + innerLookX, cy + innerLookY, 9 * scale, 16 * scale, 0, 0, Math.PI * 2);
    ctx.fill();
    
    // Right Iris
    ctx.beginPath();
    ctx.ellipse(cx + 35 * scale + innerLookX, cy + innerLookY, 9 * scale, 16 * scale, 0, 0, Math.PI * 2);
    ctx.fill();

    // Pupils
    ctx.fillStyle = this.colors.eyeIrisDark;
    ctx.beginPath();
    ctx.arc(cx - 35 * scale + innerLookX, cy + innerLookY, 4 * scale, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(cx + 35 * scale + innerLookX, cy + innerLookY, 4 * scale, 0, Math.PI * 2);
    ctx.fill();

    // Catchlights (Reflections, mostly static relative to eye)
    ctx.fillStyle = this.colors.eyeWhite;
    ctx.beginPath();
    ctx.arc(cx - 38 * scale + innerLookX, cy - 5 * scale + innerLookY, 3 * scale, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(cx + 32 * scale + innerLookX, cy - 5 * scale + innerLookY, 3 * scale, 0, Math.PI * 2);
    ctx.fill();
    
    // Eyelashes / top outline
    ctx.strokeStyle = this.colors.hairLine;
    ctx.lineWidth = 4 * scale;
    ctx.lineCap = 'round';
    
    // Left eyelash
    ctx.beginPath();
    ctx.moveTo(cx - 55 * scale, cy - eyeHeight * 0.2);
    ctx.quadraticCurveTo(cx - 35 * scale, cy - eyeHeight * 1.2, cx - 15 * scale, cy - eyeHeight * 0.5);
    ctx.stroke();
    
    // Right eyelash
    ctx.beginPath();
    ctx.moveTo(cx + 15 * scale, cy - eyeHeight * 0.5);
    ctx.quadraticCurveTo(cx + 35 * scale, cy - eyeHeight * 1.2, cx + 55 * scale, cy - eyeHeight * 0.2);
    ctx.stroke();

    // Eyebrows
    ctx.lineWidth = 2 * scale;
    let browOffsetLeft = 0;
    let browOffsetRight = 0;
    
    if (this.state.emotion === 'sad') {
      browOffsetLeft = -10 * scale;
      browOffsetRight = -10 * scale;
    } else if (this.state.emotion === 'curious') {
      browOffsetLeft = -5 * scale;
      browOffsetRight = -15 * scale;
    } else if (this.state.emotion === 'teasing') {
      browOffsetLeft = -5 * scale;
      browOffsetRight = 5 * scale;
    }

    ctx.beginPath();
    ctx.moveTo(cx - 50 * scale, cy - 35 * scale - browOffsetLeft);
    ctx.quadraticCurveTo(cx - 35 * scale, cy - 45 * scale, cx - 20 * scale, cy - 38 * scale + browOffsetLeft);
    ctx.stroke();
    
    ctx.beginPath();
    ctx.moveTo(cx + 20 * scale, cy - 38 * scale + browOffsetRight);
    ctx.quadraticCurveTo(cx + 35 * scale, cy - 45 * scale, cx + 50 * scale, cy - 35 * scale - browOffsetRight);
    ctx.stroke();
  }

  drawBlush(ctx, cx, cy, scale) {
    let blushIntensity = 0.3;
    if (this.state.emotion === 'teasing' || this.state.emotion === 'excited') {
      blushIntensity = 0.6;
    }
    
    ctx.fillStyle = `rgba(255, 100, 150, ${blushIntensity})`;
    ctx.beginPath();
    ctx.ellipse(cx - 45 * scale, cy + 25 * scale, 15 * scale, 8 * scale, -Math.PI / 8, 0, Math.PI * 2);
    ctx.fill();
    
    ctx.beginPath();
    ctx.ellipse(cx + 45 * scale, cy + 25 * scale, 15 * scale, 8 * scale, Math.PI / 8, 0, Math.PI * 2);
    ctx.fill();
  }

  drawMouth(ctx, cx, cy, scale, mouthOpen) {
    ctx.fillStyle = '#ff8899';
    ctx.strokeStyle = this.colors.hairLine;
    ctx.lineWidth = 2 * scale;

    ctx.beginPath();
    if (this.state.emotion === 'sad') {
      ctx.moveTo(cx - 10 * scale, cy + 60 * scale);
      ctx.quadraticCurveTo(cx, cy + 55 * scale, cx + 10 * scale, cy + 60 * scale);
    } else if (this.state.emotion === 'teasing') {
      ctx.moveTo(cx - 15 * scale, cy + 55 * scale);
      ctx.quadraticCurveTo(cx, cy + 60 * scale, cx + 10 * scale, cy + 52 * scale);
    } else {
      ctx.moveTo(cx - 10 * scale, cy + 55 * scale);
      ctx.quadraticCurveTo(cx, cy + 60 * scale, cx + 10 * scale, cy + 55 * scale);
      
      if (mouthOpen > 0) {
        ctx.quadraticCurveTo(cx, cy + 55 * scale + mouthOpen, cx - 10 * scale, cy + 55 * scale);
        ctx.fill();
      }
    }
    ctx.stroke();
  }

  drawParticles(ctx, width, height, time, scale) {
    // Optional: Draw emotion particles (sweat drops, hearts, stars)
    if (this.state.emotion === 'excited') {
      ctx.fillStyle = '#ffd700';
      const starY = height * 0.2 + Math.sin(time * 5) * 10;
      this.drawStar(ctx, width * 0.7, starY, 5, 15 * scale, 7 * scale);
      this.drawStar(ctx, width * 0.3, starY + 20, 5, 10 * scale, 5 * scale);
    } else if (this.state.emotion === 'sad') {
      ctx.fillStyle = 'rgba(100, 200, 255, 0.7)';
      ctx.beginPath();
      const dropY = height * 0.3 + (time * 50) % 100;
      ctx.ellipse(width * 0.65, dropY, 5 * scale, 10 * scale, 0, 0, Math.PI * 2);
      ctx.fill();
    }
  }
  
  drawStar(ctx, cx, cy, spikes, outerRadius, innerRadius) {
    let rot = Math.PI / 2 * 3;
    let x = cx;
    let y = cy;
    let step = Math.PI / spikes;

    ctx.beginPath();
    ctx.moveTo(cx, cy - outerRadius);
    for (let i = 0; i < spikes; i++) {
        x = cx + Math.cos(rot) * outerRadius;
        y = cy + Math.sin(rot) * outerRadius;
        ctx.lineTo(x, y);
        rot += step;

        x = cx + Math.cos(rot) * innerRadius;
        y = cy + Math.sin(rot) * innerRadius;
        ctx.lineTo(x, y);
        rot += step;
    }
    ctx.lineTo(cx, cy - outerRadius);
    ctx.closePath();
    ctx.fill();
  }
}
