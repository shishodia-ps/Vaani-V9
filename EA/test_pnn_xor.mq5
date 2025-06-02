#include <class_PNN.mqh>
//+------------------------------------------------------------------+
double ivect[2];  // input vector
// the data for network teaching for the "XOR" function
double inpps[]= {1,1,1,0,0,1,0,0};  // input teaching data array
double tchs[]= {0,1,1,0};           // output teaching data array
//+------------------------------------------------------------------+
void OnStart()
{
   // network creation
   CNetPNN* net=new CNetPNN(2,2);
   // network teaching
   net.Learn(4,inpps,tchs,100,1.0e-8);
   Print("MSE=",net.mse);
   // save neural network in the file
   int h=FileOpen("primer.net",FILE_BIN|FILE_WRITE);
   net.Save(h);
   FileClose(h);
   // deleting network
   delete net;
   // creating network again and downloading network from the file
   net=new CNetPNN(2,2);
   h=FileOpen("primer.net",FILE_BIN|FILE_READ);
   net.Load(h);
   FileClose(h);
   // network checking
   int out;
   string s="Check >> ";
   for(int i=0,j=0; i<4; i++)
   {
      ivect[0]=inpps[j++]; ivect[1]=inpps[j++];
      out=net.Calculate(ivect);
      s+=" "+(string)ivect[0]+" xor "+(string)ivect[1]+" = "+(string)out+"("+(string)tchs[i]+") // ";
   }
   Print(s);
   // тест 1
   s="Test 1 >> ";
   double in2[]= {0.9,0.9,0.9,0.1,0.1,0.9,0.1,0.1}; // input test data array
   for(int i=0,j=0; i<4; i++)
   {
      ivect[0]=in2[j++]; ivect[1]=in2[j++];
      out=net.Calculate(ivect);
      s+=" "+(string)ivect[0]+" xor "+(string)ivect[1]+" = "+(string)out+"("+(string)tchs[i]+") // ";
   }
   Print(s);
   // тест 2
   s="Test 1 >> ";
   double in3[]= {0.8,0.8,0.8,0.2,0.2,0.8,0.2,0.2}; // input test data array
   for(int i=0,j=0; i<4; i++)
   {
      ivect[0]=in3[j++]; ivect[1]=in3[j++];
      out=net.Calculate(ivect);
      s+=" "+(string)ivect[0]+" xor "+(string)ivect[1]+" = "+(string)out+"("+(string)tchs[i]+") // ";
   }
   Print(s);
   // deleting network
   delete net;
   FileDelete("primer.net");
}
//+------------------------------------------------------------------+
