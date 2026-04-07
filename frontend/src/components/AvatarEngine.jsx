import { useEffect, useRef } from 'react';
import { MarinCanvasEngine } from '../engine/avatar.js';

export default function AvatarEngine({ emotion, isSpeaking }) {
  const canvasRef = useRef(null);
  const engineRef = useRef(null);

  useEffect(() => {
    if (!canvasRef.current) return;

    // Initialize engine
    const canvas = canvasRef.current;
    
    // Set internal resolution based on CSS size for sharp rendering
    const updateSize = () => {
      const rect = canvas.parentElement.getBoundingClientRect();
      const styleWidth = rect.width;
      const styleHeight = rect.height;
      const dpr = window.devicePixelRatio || 1;
      
      canvas.width = styleWidth * dpr;
      canvas.height = styleHeight * dpr;
      
      // Keep CSS size
      canvas.style.width = `${styleWidth}px`;
      canvas.style.height = `${styleHeight}px`;
    };
    
    updateSize();
    window.addEventListener('resize', updateSize);

    engineRef.current = new MarinCanvasEngine(canvas);
    engineRef.current.start();

    // Setup mouse tracking
    const handleMouseMove = (e) => {
        if (!engineRef.current || !canvasRef.current) return;
        const rect = canvasRef.current.getBoundingClientRect();
        const maxDist = 200; // max pixel distance the eyes will track
        
        // Calculate bounded mouse position relative to canvas center
        let targetX = e.clientX - (rect.left + rect.width / 2);
        let targetY = e.clientY - (rect.top + rect.height / 2);
        
        // Cap the distance
        const dist = Math.sqrt(targetX*targetX + targetY*targetY);
        if (dist > maxDist) {
            targetX = (targetX / dist) * maxDist;
            targetY = (targetY / dist) * maxDist;
        }
        
        // Offset so 0,0 is center
        engineRef.current.setState({ 
            mousePos: { 
                x: targetX + canvas.width/2, 
                y: targetY + canvas.height/2 
            } 
        });
    };
    window.addEventListener('mousemove', handleMouseMove);

    return () => {
      window.removeEventListener('resize', updateSize);
      window.removeEventListener('mousemove', handleMouseMove);
      if (engineRef.current) {
        engineRef.current.stop();
      }
    };
  }, []);

  useEffect(() => {
    if (engineRef.current) {
      engineRef.current.setState({ emotion, isSpeaking });
    }
  }, [emotion, isSpeaking]);

  return (
    <canvas 
        ref={canvasRef} 
        className="w-full h-full"
        style={{ touchAction: 'none' }}
    />
  );
}
